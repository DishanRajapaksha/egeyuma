import { base } from '$app/paths';

export const prerender = true;

type ResultItem = {
  id: string;
  gold: string;
  prediction: string | null;
  raw_response: string;
  correct: boolean;
  subject: string | null;
  domain: string | null;
  difficulty: string | null;
  language_style: string;
  source: string | null;
};

type ResultPayload = {
  run_id: string;
  framework: string;
  engine: string;
  model: string;
  task: string;
  dataset: string;
  prompt_version: string;
  total: number;
  correct: number;
  accuracy: number;
  invalid_response_count: number;
  invalid_response_rate: number;
  breakdowns: Record<string, Record<string, number>>;
  items: ResultItem[];
};

type ResultIndex = {
  runs: Array<{
    filename: string;
    modified_at: string;
  }>;
};

type DashboardRun = ResultPayload & {
  filename: string;
  modified_at: string;
};

type InvalidResultFile = {
  filename: string;
  reason: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object';
}

function isNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function isResultPayload(value: unknown): value is ResultPayload {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.run_id === 'string' &&
    typeof value.engine === 'string' &&
    typeof value.model === 'string' &&
    typeof value.dataset === 'string' &&
    typeof value.prompt_version === 'string' &&
    isNumber(value.total) &&
    isNumber(value.correct) &&
    isNumber(value.accuracy) &&
    isNumber(value.invalid_response_count) &&
    isNumber(value.invalid_response_rate) &&
    isRecord(value.breakdowns) &&
    Array.isArray(value.items)
  );
}

async function fetchJson<T>(fetchFn: typeof fetch, path: string): Promise<T> {
  const response = await fetchFn(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path}: ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function load({ fetch }: { fetch: typeof globalThis.fetch }) {
  const resultsPath = `${base}/results`;
  const invalidResults: InvalidResultFile[] = [];

  try {
    const index = await fetchJson<ResultIndex>(fetch, `${resultsPath}/index.json`);
    const runs = await Promise.all(
      index.runs.map(async (entry) => {
        try {
          const payload = await fetchJson<unknown>(fetch, `${resultsPath}/${entry.filename}`);
          if (!isResultPayload(payload)) {
            invalidResults.push({
              filename: entry.filename,
              reason: 'Unsupported or incomplete result schema'
            });
            return null;
          }

          return {
            ...payload,
            filename: entry.filename,
            modified_at: entry.modified_at
          };
        } catch (error) {
          invalidResults.push({
            filename: entry.filename,
            reason: error instanceof Error ? error.message : 'Could not parse result file'
          });
          return null;
        }
      })
    );

    return {
      resultsPath,
      loadError: null,
      invalidResults,
      runs: runs
        .filter((run): run is DashboardRun => run !== null)
        .sort((left, right) => right.modified_at.localeCompare(left.modified_at))
    };
  } catch (error) {
    return {
      resultsPath,
      loadError: error instanceof Error ? error.message : 'Could not load result index',
      invalidResults,
      runs: [] satisfies DashboardRun[]
    };
  }
}
