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

function isResultPayload(value: unknown): value is ResultPayload {
  if (!value || typeof value !== 'object') {
    return false;
  }

  const candidate = value as Partial<ResultPayload>;
  return (
    typeof candidate.run_id === 'string' &&
    typeof candidate.model === 'string' &&
    typeof candidate.total === 'number' &&
    typeof candidate.correct === 'number' &&
    typeof candidate.accuracy === 'number' &&
    Array.isArray(candidate.items)
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

  try {
    const index = await fetchJson<ResultIndex>(fetch, `${resultsPath}/index.json`);
    const runs = await Promise.all(
      index.runs.map(async (entry) => {
        const payload = await fetchJson<unknown>(fetch, `${resultsPath}/${entry.filename}`);
        if (!isResultPayload(payload)) {
          return null;
        }

        return {
          ...payload,
          filename: entry.filename,
          modified_at: entry.modified_at
        };
      })
    );

    return {
      resultsPath,
      runs: runs
        .filter((run): run is DashboardRun => run !== null)
        .sort((left, right) => right.modified_at.localeCompare(left.modified_at))
    };
  } catch {
    return {
      resultsPath,
      runs: [] satisfies DashboardRun[]
    };
  }
}
