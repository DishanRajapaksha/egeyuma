<script lang="ts">
  const cards = [
    { label: 'Runs', value: '0', help: 'Import result JSON files from the engine.' },
    { label: 'Best accuracy', value: '—', help: 'No benchmark results loaded yet.' },
    { label: 'Datasets', value: '0', help: 'SinhalaMMLU support is the first target.' }
  ];
</script>

<svelte:head>
  <title>Egeyuma Dashboard</title>
  <meta
    name="description"
    content="Dashboard for Sinhala, Singlish, and Sri Lankan-context LLM evaluation results."
  />
</svelte:head>

<main class="shell">
  <section class="hero">
    <p class="eyebrow">Egeyuma Dashboard</p>
    <h1>Sinhala LLM evaluation, without the spreadsheet swamp.</h1>
    <p class="lede">
      This dashboard will visualise engine result JSON files, compare model accuracy, and surface
      subject-level weaknesses across SinhalaMMLU-style benchmarks.
    </p>
  </section>

  <section class="cards" aria-label="Dashboard summary">
    {#each cards as card}
      <article class="card">
        <span>{card.label}</span>
        <strong>{card.value}</strong>
        <p>{card.help}</p>
      </article>
    {/each}
  </section>

  <section class="panel">
    <h2>Next dashboard slice</h2>
    <ul>
      <li>Load Egeyuma result JSON files.</li>
      <li>Render overall accuracy and invalid response rate.</li>
      <li>Compare accuracy by subject, domain, difficulty, and language style.</li>
      <li>Link out to Inspect logs for sample-level debugging.</li>
    </ul>
  </section>
</main>
