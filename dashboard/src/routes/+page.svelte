<script lang="ts">
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

  type PageData = {
    resultsPath: string;
    runs: DashboardRun[];
  };

  const { data }: { data: PageData } = $props();
  const latest = $derived(data.runs[0]);
  const runCount = $derived(data.runs.length);
  const sortedByAccuracy = $derived(
    [...data.runs].sort((left, right) => {
      const accuracyDiff = right.accuracy - left.accuracy;
      if (accuracyDiff !== 0) {
        return accuracyDiff;
      }
      return right.modified_at.localeCompare(left.modified_at);
    })
  );
  const bestAccuracy = $derived(
    runCount === 0 ? 0 : Math.max(...data.runs.map((run) => run.accuracy))
  );

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;
  const formatDate = (value: string) =>
    new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short'
    }).format(new Date(value));

  const breakdownEntries = (run: DashboardRun) =>
    Object.entries(run.breakdowns).flatMap(([group, values]) =>
      Object.entries(values).map(([label, accuracy]) => ({ group, label, accuracy }))
    );
</script>

<svelte:head>
  <title>Egeyuma Dashboard</title>
  <meta
    name="description"
    content="Dashboard for Sinhala, Singlish, and Sri Lankan-context LLM evaluation results."
  />
</svelte:head>

<main class="app-shell">
  <header class="topbar">
    <div>
      <p class="eyebrow">Egeyuma</p>
      <h1>LLM Benchmark Dashboard</h1>
    </div>
    <div class="source-path">
      <span>Published results</span>
      <code>{data.resultsPath}</code>
    </div>
  </header>

  <section class="summary-grid" aria-label="Benchmark summary">
    <article class="metric">
      <span>Runs</span>
      <strong>{runCount}</strong>
      <p>JSON artifacts loaded</p>
    </article>
    <article class="metric">
      <span>Best accuracy</span>
      <strong>{runCount === 0 ? '—' : formatPercent(bestAccuracy)}</strong>
      <p>Top run in directory</p>
    </article>
    <article class="metric">
      <span>Latest accuracy</span>
      <strong>{latest ? formatPercent(latest.accuracy) : '—'}</strong>
      <p>{latest ? `${latest.correct}/${latest.total} correct` : 'No completed run'}</p>
    </article>
    <article class="metric">
      <span>Latest invalid</span>
      <strong>{latest ? formatPercent(latest.invalid_response_rate) : '—'}</strong>
      <p>{latest ? `${latest.invalid_response_count} invalid responses` : 'No completed run'}</p>
    </article>
  </section>

  {#if latest}
    <section class="content-grid">
      <article class="panel leaderboard">
        <div class="section-heading">
          <div>
            <h2>Leaderboard</h2>
            <p>Ranked by accuracy, then latest run.</p>
          </div>
          <span class="count">{sortedByAccuracy.length} runs</span>
        </div>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Rank</th>
                <th>Model</th>
                <th>Accuracy</th>
                <th>Correct</th>
                <th>Invalid</th>
                <th>Engine</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {#each sortedByAccuracy as run, index}
                <tr class:highlight={run.filename === latest.filename}>
                  <td>{index + 1}</td>
                  <td>
                    <strong>{run.model}</strong>
                    <small>{run.filename}</small>
                  </td>
                  <td>{formatPercent(run.accuracy)}</td>
                  <td>{run.correct}/{run.total}</td>
                  <td>{formatPercent(run.invalid_response_rate)}</td>
                  <td>{run.engine}</td>
                  <td>{formatDate(run.modified_at)}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </article>

      <aside class="panel run-card">
        <div class="section-heading">
          <div>
            <h2>Latest Run</h2>
            <p>{latest.filename}</p>
          </div>
        </div>

        <div class="accuracy-ring">
          <strong>{formatPercent(latest.accuracy)}</strong>
          <span>{latest.correct}/{latest.total}</span>
        </div>

        <dl class="metadata-grid compact">
          <div>
            <dt>Model</dt>
            <dd>{latest.model}</dd>
          </div>
          <div>
            <dt>Dataset</dt>
            <dd>{latest.dataset}</dd>
          </div>
          <div>
            <dt>Prompt</dt>
            <dd>{latest.prompt_version}</dd>
          </div>
          <div>
            <dt>Run ID</dt>
            <dd>{latest.run_id}</dd>
          </div>
        </dl>
      </aside>
    </section>

    <section class="panel">
      <div class="section-heading">
        <div>
          <h2>Breakdowns</h2>
          <p>Accuracy by subject, domain, difficulty, and language style.</p>
        </div>
      </div>

      <div class="breakdown-grid">
        {#each breakdownEntries(latest) as item}
          <article class="breakdown">
            <div>
              <span>{item.group}</span>
              <strong>{item.label}</strong>
            </div>
            <div class="bar" style={`--value: ${item.accuracy * 100}%`}>
              <span></span>
            </div>
            <small>{formatPercent(item.accuracy)}</small>
          </article>
        {/each}
      </div>
    </section>

    <section class="panel">
      <div class="section-heading">
        <div>
          <h2>Samples</h2>
          <p>Gold labels, predictions, and response validity.</p>
        </div>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Item</th>
              <th>Subject</th>
              <th>Gold</th>
              <th>Prediction</th>
              <th>Status</th>
              <th>Raw</th>
            </tr>
          </thead>
          <tbody>
            {#each latest.items as item}
              <tr>
                <td>
                  <code>{item.id}</code>
                </td>
                <td>{item.subject ?? 'unknown'}</td>
                <td>{item.gold}</td>
                <td>{item.prediction ?? 'invalid'}</td>
                <td>
                  <span class="status" class:ok={item.correct} class:bad={!item.correct}>
                    {item.correct ? 'correct' : 'wrong'}
                  </span>
                </td>
                <td>{item.raw_response || 'empty'}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </section>
  {:else}
    <section class="panel empty">
      <h2>No result files found</h2>
      <p>Publish result JSON files into {data.resultsPath}.</p>
    </section>
  {/if}
</main>
