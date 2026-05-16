<script lang="ts">
  import { base } from '$app/paths';

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

  type DashboardRun = {
    filename: string;
    modified_at: string;
    run_id: string;
    engine: string;
    model: string;
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

  type InvalidResultFile = {
    filename: string;
    reason: string;
  };

  type PageData = {
    resultsPath: string;
    loadError: string | null;
    invalidResults: InvalidResultFile[];
    runs: DashboardRun[];
  };

  type RunKind = 'benchmark' | 'smoke';
  type SortKey = 'accuracy' | 'updated' | 'questions' | 'invalid' | 'model';
  type SampleTab = 'wrong' | 'invalid' | 'all';

  type DecoratedRun = DashboardRun & {
    kind: RunKind;
    displayModel: string;
    displayDataset: string;
    displayLabel: string;
  };

  const { data }: { data: PageData } = $props();

  const docsHref = $derived(`${base}/docs/`);
  const githubHref = 'https://github.com/DishanRajapaksha/egeyuma';
  const resultsHref = $derived(data.resultsPath);

  let kindFilter = $state<'benchmark' | 'smoke' | 'all'>('benchmark');
  let datasetFilter = $state('all');
  let engineFilter = $state('all');
  let promptFilter = $state('all');
  let minQuestions = $state(50);
  let sortKey = $state<SortKey>('accuracy');
  let selectedFilename = $state<string>('');
  let compareLeftFilename = $state<string>('');
  let compareRightFilename = $state<string>('');
  let sampleTab = $state<SampleTab>('wrong');

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;
  const formatSignedPercent = (value: number) => `${value >= 0 ? '+' : ''}${(value * 100).toFixed(1)}%`;
  const formatDate = (value: string) =>
    new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short'
    }).format(new Date(value));

  function titleCase(value: string): string {
    return value
      .split(/[-_/\s]+/)
      .filter(Boolean)
      .map((part) => part.slice(0, 1).toUpperCase() + part.slice(1))
      .join(' ');
  }

  function displayModelName(model: string): string {
    const raw = model.split('/').at(-1) ?? model;
    return titleCase(raw.replace(/^google-/, '').replace(/^lmstudio-/, ''));
  }

  function displayDatasetName(dataset: string, filename: string): string {
    const value = `${dataset} ${filename}`.toLowerCase();
    if (value.includes('sinhalammlu')) return 'SinhalaMMLU';
    if (value.includes('sample')) return 'Sample';
    return titleCase(dataset.split('/').at(-1) ?? dataset);
  }

  function runKind(run: DashboardRun): RunKind {
    const name = `${run.dataset} ${run.filename}`.toLowerCase();
    return run.total >= 50 && !name.includes('sample') ? 'benchmark' : 'smoke';
  }

  function decorateRun(run: DashboardRun): DecoratedRun {
    const displayModel = displayModelName(run.model);
    const displayDataset = displayDatasetName(run.dataset, run.filename);
    return {
      ...run,
      kind: runKind(run),
      displayModel,
      displayDataset,
      displayLabel: `${displayModel} · ${displayDataset} · ${run.total} questions`
    };
  }

  function unique(values: string[]): string[] {
    return [...new Set(values)].sort((left, right) => left.localeCompare(right));
  }

  function isInvalidItem(item: ResultItem): boolean {
    return item.prediction === null || item.prediction === '';
  }

  function breakdownGroups(run: DecoratedRun) {
    return Object.entries(run.breakdowns).map(([group, values]) => ({
      group,
      entries: Object.entries(values)
        .map(([label, accuracy]) => ({ label, accuracy }))
        .sort((left, right) => left.accuracy - right.accuracy || left.label.localeCompare(right.label))
    }));
  }

  function sampleItems(run: DecoratedRun, tab: SampleTab): ResultItem[] {
    if (tab === 'wrong') return run.items.filter((item) => !item.correct && !isInvalidItem(item));
    if (tab === 'invalid') return run.items.filter(isInvalidItem);
    return run.items;
  }

  function compareRuns(left: DecoratedRun | undefined, right: DecoratedRun | undefined) {
    if (!left || !right) return null;

    const leftItems = new Map(left.items.map((item) => [item.id, item]));
    const shared = right.items
      .map((rightItem) => ({ leftItem: leftItems.get(rightItem.id), rightItem }))
      .filter((pair): pair is { leftItem: ResultItem; rightItem: ResultItem } => Boolean(pair.leftItem));

    return {
      accuracyDelta: right.accuracy - left.accuracy,
      invalidDelta: right.invalid_response_rate - left.invalid_response_rate,
      correctDelta: right.correct - left.correct,
      improved: shared.filter((pair) => !pair.leftItem.correct && pair.rightItem.correct).length,
      regressed: shared.filter((pair) => pair.leftItem.correct && !pair.rightItem.correct).length,
      sharedWrong: shared.filter((pair) => !pair.leftItem.correct && !pair.rightItem.correct).length,
      sharedCount: shared.length
    };
  }

  function selectRun(filename: string) {
    selectedFilename = filename;
  }

  function selectRunFromKeyboard(event: KeyboardEvent, filename: string) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      selectRun(filename);
    }
  }

  const runs = $derived(data.runs.map(decorateRun));
  const benchmarkRuns = $derived(runs.filter((run) => run.kind === 'benchmark'));
  const smokeRuns = $derived(runs.filter((run) => run.kind === 'smoke'));
  const visibleRunPool = $derived(kindFilter === 'benchmark' ? benchmarkRuns : kindFilter === 'smoke' ? smokeRuns : runs);
  const datasets = $derived(unique(runs.map((run) => run.displayDataset)));
  const engines = $derived(unique(runs.map((run) => run.engine)));
  const prompts = $derived(unique(runs.map((run) => run.prompt_version)));
  const latest = $derived(runs[0]);
  const lastUpdated = $derived(
    runs.length === 0 ? null : runs.reduce((latestRun, run) => (run.modified_at > latestRun.modified_at ? run : latestRun), runs[0])
  );
  const filteredRuns = $derived.by(() =>
    visibleRunPool.filter(
      (run) =>
        (datasetFilter === 'all' || run.displayDataset === datasetFilter) &&
        (engineFilter === 'all' || run.engine === engineFilter) &&
        (promptFilter === 'all' || run.prompt_version === promptFilter) &&
        run.total >= minQuestions
    )
  );
  const sortedRuns = $derived.by(() =>
    [...filteredRuns].sort((left, right) => {
      if (sortKey === 'updated') return right.modified_at.localeCompare(left.modified_at);
      if (sortKey === 'questions') return right.total - left.total || right.accuracy - left.accuracy;
      if (sortKey === 'invalid') return left.invalid_response_rate - right.invalid_response_rate || right.accuracy - left.accuracy;
      if (sortKey === 'model') return left.displayModel.localeCompare(right.displayModel) || right.accuracy - left.accuracy;
      return right.accuracy - left.accuracy || right.total - left.total || right.modified_at.localeCompare(left.modified_at);
    })
  );
  const selectedRun = $derived(runs.find((run) => run.filename === selectedFilename) ?? sortedRuns[0] ?? runs[0]);
  const selectedBreakdowns = $derived(selectedRun ? breakdownGroups(selectedRun) : []);
  const selectedSampleItems = $derived(selectedRun ? sampleItems(selectedRun, sampleTab) : []);
  const bestBenchmarkAccuracy = $derived(benchmarkRuns.length === 0 ? 0 : Math.max(...benchmarkRuns.map((run) => run.accuracy)));
  const trendRuns = $derived([...benchmarkRuns].sort((left, right) => left.modified_at.localeCompare(right.modified_at)).slice(-12));
  const compareLeft = $derived(runs.find((run) => run.filename === compareLeftFilename) ?? runs[0]);
  const compareRight = $derived(runs.find((run) => run.filename === compareRightFilename) ?? runs[1] ?? runs[0]);
  const comparison = $derived(compareRuns(compareLeft, compareRight));

  $effect(() => {
    const firstRun = runs[0]?.filename ?? '';
    const secondRun = runs[1]?.filename ?? firstRun;

    if (!selectedFilename && firstRun) {
      selectedFilename = firstRun;
    }

    if (!compareLeftFilename && firstRun) {
      compareLeftFilename = firstRun;
    }

    if (!compareRightFilename && secondRun) {
      compareRightFilename = secondRun;
    }
  });
</script>

<svelte:head>
  <title>Egeyuma Dashboard</title>
  <meta name="description" content="Dashboard for Sinhala, Singlish, and Sri Lankan-context LLM evaluation results." />
</svelte:head>

<main class="app-shell">
  <header class="topbar">
    <div>
      <p class="eyebrow">Egeyuma</p>
      <h1>LLM Benchmark Dashboard</h1>
      <p class="lede">Sinhala and Sri Lankan-context LLM evaluation results.</p>
    </div>
    <div class="topbar-actions">
      <a class="docs-link" href={docsHref}>Docs</a>
      <a class="docs-link" href={githubHref}>GitHub</a>
      <a class="docs-link" href={resultsHref}>Results JSON</a>
      <div class="source-path">
        <span>Last updated</span>
        <code>{lastUpdated ? formatDate(lastUpdated.modified_at) : 'No runs yet'}</code>
      </div>
    </div>
  </header>

  {#if data.loadError || data.invalidResults.length > 0}
    <section class="panel warning-panel" aria-label="Result loading warnings">
      <div>
        <h2>Result loading warnings</h2>
        <p>Bad files are shown here instead of silently disappearing.</p>
      </div>
      {#if data.loadError}
        <p class="warning-line">{data.loadError}</p>
      {/if}
      {#if data.invalidResults.length > 0}
        <ul>
          {#each data.invalidResults as file}
            <li><code>{file.filename}</code>: {file.reason}</li>
          {/each}
        </ul>
      {/if}
    </section>
  {/if}

  <section class="summary-grid" aria-label="Benchmark summary">
    <article class="metric">
      <span>Benchmark runs</span>
      <strong>{benchmarkRuns.length}</strong>
      <p>{smokeRuns.length} smoke runs separated</p>
    </article>
    <article class="metric">
      <span>Best benchmark</span>
      <strong>{benchmarkRuns.length === 0 ? 'N/A' : formatPercent(bestBenchmarkAccuracy)}</strong>
      <p>Smoke tests excluded</p>
    </article>
    <article class="metric">
      <span>Latest accuracy</span>
      <strong>{latest ? formatPercent(latest.accuracy) : 'N/A'}</strong>
      <p>{latest ? `${latest.correct}/${latest.total} correct, ${latest.displayDataset}` : 'No completed run'}</p>
    </article>
    <article class="metric">
      <span>Latest invalid</span>
      <strong>{latest ? formatPercent(latest.invalid_response_rate) : 'N/A'}</strong>
      <p>{latest ? `${latest.invalid_response_count} invalid responses` : 'No completed run'}</p>
    </article>
  </section>

  {#if runs.length > 0}
    <section class="panel controls-panel" aria-label="Filters and sorting">
      <div class="control-group">
        <label>Run type<select bind:value={kindFilter}><option value="benchmark">Benchmarks</option><option value="smoke">Smoke tests</option><option value="all">All runs</option></select></label>
        <label>Dataset<select bind:value={datasetFilter}><option value="all">All datasets</option>{#each datasets as dataset}<option value={dataset}>{dataset}</option>{/each}</select></label>
        <label>Engine<select bind:value={engineFilter}><option value="all">All engines</option>{#each engines as engine}<option value={engine}>{engine}</option>{/each}</select></label>
        <label>Prompt<select bind:value={promptFilter}><option value="all">All prompts</option>{#each prompts as prompt}<option value={prompt}>{prompt}</option>{/each}</select></label>
        <label>Min questions<input type="number" min="0" step="1" bind:value={minQuestions} /></label>
        <label>Sort by<select bind:value={sortKey}><option value="accuracy">Accuracy</option><option value="updated">Updated</option><option value="questions">Question count</option><option value="invalid">Invalid rate</option><option value="model">Model name</option></select></label>
      </div>
    </section>

    <section class="content-grid">
      <article class="panel leaderboard">
        <div class="section-heading">
          <div>
            <h2>Leaderboard</h2>
            <p>Smoke tests are separated from real benchmark runs.</p>
          </div>
          <span class="count">{sortedRuns.length} runs</span>
        </div>

        {#if sortedRuns.length > 0}
          <div class="table-wrap">
            <table>
              <thead><tr><th>Rank</th><th>Model</th><th>Dataset</th><th>Questions</th><th>Accuracy</th><th>Invalid</th><th>Prompt</th><th>Engine</th><th>Updated</th></tr></thead>
              <tbody>
                {#each sortedRuns as run, index}
                  <tr class:selected={selectedRun && run.filename === selectedRun.filename} tabindex="0" role="button" aria-pressed={Boolean(selectedRun && run.filename === selectedRun.filename)} aria-label={`Select ${run.displayLabel}`} onclick={() => selectRun(run.filename)} onkeydown={(event) => selectRunFromKeyboard(event, run.filename)}>
                    <td>{index + 1}</td>
                    <td><strong>{run.displayModel}</strong><small>{run.model}</small></td>
                    <td><strong>{run.displayDataset}</strong><small>{run.kind}</small></td>
                    <td>{run.total}</td>
                    <td>{formatPercent(run.accuracy)}</td>
                    <td>{formatPercent(run.invalid_response_rate)}</td>
                    <td>{run.prompt_version}</td>
                    <td>{run.engine}</td>
                    <td>{formatDate(run.modified_at)}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {:else}
          <div class="empty compact-empty"><h2>No runs match these filters</h2><p>Lower the minimum question count or switch run type.</p></div>
        {/if}
      </article>

      {#if selectedRun}
        <aside class="panel run-card">
          <div class="section-heading"><div><h2>Selected Run</h2><p>{selectedRun.displayLabel}</p></div></div>
          <label class="wide-label">Selected run<select bind:value={selectedFilename}>{#each sortedRuns.length > 0 ? sortedRuns : runs as run}<option value={run.filename}>{run.displayLabel}</option>{/each}</select></label>
          <div class="accuracy-ring"><strong>{formatPercent(selectedRun.accuracy)}</strong><span>{selectedRun.correct}/{selectedRun.total}</span></div>
          <dl class="metadata-grid compact">
            <div><dt>Model</dt><dd><strong>{selectedRun.displayModel}</strong><small>{selectedRun.model}</small></dd></div>
            <div><dt>Dataset</dt><dd><strong>{selectedRun.displayDataset}</strong><small>{selectedRun.dataset}</small></dd></div>
            <div><dt>Questions</dt><dd>{selectedRun.correct}/{selectedRun.total} correct</dd></div>
            <div><dt>Invalid</dt><dd>{selectedRun.invalid_response_count}, {formatPercent(selectedRun.invalid_response_rate)}</dd></div>
            <div><dt>Prompt</dt><dd>{selectedRun.prompt_version}</dd></div>
            <div><dt>Run ID</dt><dd>{selectedRun.run_id}</dd></div>
          </dl>
        </aside>
      {/if}
    </section>

    {#if selectedRun}
      <section class="panel">
        <div class="section-heading"><div><h2>Breakdowns</h2><p>Grouped by dimension and sorted by weakest accuracy first.</p></div></div>
        <div class="breakdown-sections">
          {#each selectedBreakdowns as group}
            <section><h3>{group.group}</h3><div class="breakdown-grid">{#each group.entries as item}<article class="breakdown"><div><strong>{item.label}</strong></div><div class="bar" style={`--value: ${item.accuracy * 100}%`}><span></span></div><small>{formatPercent(item.accuracy)}</small></article>{/each}</div></section>
          {/each}
        </div>
      </section>

      <section class="panel compare-panel">
        <div class="section-heading"><div><h2>Compare Runs</h2><p>Compare accuracy, invalid rate, and item-level movement between two runs.</p></div></div>
        <div class="compare-selectors"><label>From<select bind:value={compareLeftFilename}>{#each runs as run}<option value={run.filename}>{run.displayLabel}</option>{/each}</select></label><label>To<select bind:value={compareRightFilename}>{#each runs as run}<option value={run.filename}>{run.displayLabel}</option>{/each}</select></label></div>
        {#if comparison}
          <div class="comparison-grid">
            <article class="mini-metric"><span>Accuracy delta</span><strong>{formatSignedPercent(comparison.accuracyDelta)}</strong></article>
            <article class="mini-metric"><span>Correct delta</span><strong>{comparison.correctDelta >= 0 ? '+' : ''}{comparison.correctDelta}</strong></article>
            <article class="mini-metric"><span>Invalid delta</span><strong>{formatSignedPercent(comparison.invalidDelta)}</strong></article>
            <article class="mini-metric"><span>Improved</span><strong>{comparison.improved}</strong></article>
            <article class="mini-metric"><span>Regressed</span><strong>{comparison.regressed}</strong></article>
            <article class="mini-metric"><span>Shared wrong</span><strong>{comparison.sharedWrong}</strong></article>
          </div>
          <p class="muted-note">Compared across {comparison.sharedCount} shared item IDs.</p>
        {/if}
      </section>

      <section class="panel">
        <div class="section-heading"><div><h2>Benchmark Trend</h2><p>Latest benchmark runs only.</p></div></div>
        {#if trendRuns.length > 0}
          <div class="trend-list">{#each trendRuns as run}<article class="trend-row"><div><strong>{run.displayModel}</strong><small>{formatDate(run.modified_at)}, {run.total} questions</small></div><div class="bar trend-bar" style={`--value: ${run.accuracy * 100}%`}><span></span></div><strong>{formatPercent(run.accuracy)}</strong></article>{/each}</div>
        {:else}
          <p class="muted-note">No benchmark runs available yet.</p>
        {/if}
      </section>

      <section class="panel">
        <div class="section-heading samples-heading"><div><h2>Samples</h2><p>Start with wrong answers, then inspect invalid or all responses.</p></div><div class="tabs" role="tablist" aria-label="Sample filters"><button class:active={sampleTab === 'wrong'} onclick={() => (sampleTab = 'wrong')}>Wrong</button><button class:active={sampleTab === 'invalid'} onclick={() => (sampleTab = 'invalid')}>Invalid</button><button class:active={sampleTab === 'all'} onclick={() => (sampleTab = 'all')}>All</button></div></div>
        {#if selectedSampleItems.length > 0}
          <div class="table-wrap"><table><thead><tr><th>Item</th><th>Subject</th><th>Gold</th><th>Prediction</th><th>Status</th><th>Raw</th></tr></thead><tbody>{#each selectedSampleItems as item}<tr><td><code>{item.id}</code></td><td>{item.subject ?? 'unknown'}</td><td>{item.gold}</td><td>{item.prediction ?? 'invalid'}</td><td><span class="status" class:ok={item.correct} class:bad={!item.correct}>{item.correct ? 'correct' : isInvalidItem(item) ? 'invalid' : 'wrong'}</span></td><td>{item.raw_response || 'empty'}</td></tr>{/each}</tbody></table></div>
        {:else}
          <div class="empty compact-empty"><h2>No {sampleTab} samples</h2><p>This run has nothing in the selected sample bucket.</p></div>
        {/if}
      </section>
    {/if}
  {:else}
    <section class="panel empty"><h2>No result files found</h2><p>Publish result JSON files into {data.resultsPath}.</p></section>
  {/if}
</main>
