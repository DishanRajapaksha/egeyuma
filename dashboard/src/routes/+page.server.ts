import { readdir, readFile, stat } from 'node:fs/promises';
import { resolve } from 'node:path';

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

type DashboardRun = ResultPayload & {
  filename: string;
  modified_at: string;
};

const resultsDir = resolve(process.env.EGEYUMA_RESULTS_DIR ?? '../results');

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

async function loadResultFile(filename: string): Promise<DashboardRun | null> {
  const path = resolve(resultsDir, filename);
  const [raw, metadata] = await Promise.all([readFile(path, 'utf-8'), stat(path)]);
  const parsed: unknown = JSON.parse(raw);

  if (!isResultPayload(parsed)) {
    return null;
  }

  return {
    ...parsed,
    filename,
    modified_at: metadata.mtime.toISOString()
  };
}

export async function load() {
  let filenames: string[] = [];

  try {
    filenames = (await readdir(resultsDir)).filter((filename) => filename.endsWith('.json'));
  } catch {
    return {
      resultsDir,
      runs: [] satisfies DashboardRun[]
    };
  }

  const loaded = await Promise.all(
    filenames.map(async (filename) => {
      try {
        return await loadResultFile(filename);
      } catch {
        return null;
      }
    })
  );

  const runs = loaded
    .filter((run): run is DashboardRun => run !== null)
    .sort((left, right) => right.modified_at.localeCompare(left.modified_at));

  return {
    resultsDir,
    runs
  };
}
