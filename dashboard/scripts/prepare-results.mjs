import { copyFile, mkdir, readdir, readFile, rm, stat, writeFile } from 'node:fs/promises';
import { basename, resolve } from 'node:path';

const repoRoot = resolve(import.meta.dirname, '../..');
const sourceDir = resolve(repoRoot, 'results/published');
const outputDir = resolve(repoRoot, 'dashboard/static/results');

function isResultPayload(value) {
  return (
    value &&
    typeof value === 'object' &&
    typeof value.run_id === 'string' &&
    typeof value.model === 'string' &&
    typeof value.total === 'number' &&
    typeof value.correct === 'number' &&
    typeof value.accuracy === 'number' &&
    Array.isArray(value.items)
  );
}

async function main() {
  await rm(outputDir, { recursive: true, force: true });
  await mkdir(outputDir, { recursive: true });

  let filenames = [];
  try {
    filenames = (await readdir(sourceDir)).filter((filename) => filename.endsWith('.json'));
  } catch {
    await writeFile(resolve(outputDir, 'index.json'), JSON.stringify({ runs: [] }, null, 2));
    return;
  }

  const runs = [];

  for (const filename of filenames.sort()) {
    const sourcePath = resolve(sourceDir, filename);
    const raw = await readFile(sourcePath, 'utf-8');
    const parsed = JSON.parse(raw);

    if (!isResultPayload(parsed)) {
      throw new Error(`${sourcePath} is not an Egeyuma result payload`);
    }

    const metadata = await stat(sourcePath);
    await copyFile(sourcePath, resolve(outputDir, filename));
    runs.push({
      filename: basename(filename),
      modified_at: metadata.mtime.toISOString()
    });
  }

  runs.sort((left, right) => right.modified_at.localeCompare(left.modified_at));
  await writeFile(resolve(outputDir, 'index.json'), JSON.stringify({ runs }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
