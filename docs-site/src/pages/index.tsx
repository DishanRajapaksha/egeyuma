import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';

export default function Home(): JSX.Element {
  return (
    <Layout
      title="Egeyuma Docs"
      description="Documentation for Sinhala and Sri Lankan-context LLM evaluation tooling"
    >
      <main className="home">
        <section className="hero hero--primary">
          <div className="container">
            <h1 className="hero__title">Egeyuma Docs</h1>
            <p className="hero__subtitle">
              Documentation for the Python evaluation engine and SvelteKit benchmark dashboard.
            </p>
          </div>
        </section>
        <section className="home__cards container">
          <Link className="home__card home__card--engine" to="/engine/">
            <span>Engine docs</span>
            <h2>Python Evaluation Engine</h2>
            <p>Dataset loading, model providers, Inspect AI, scoring, and result contracts.</p>
            <strong>Open engine docs -&gt;</strong>
          </Link>
          <Link className="home__card home__card--dashboard" to="/dashboard/">
            <span>Dashboard docs</span>
            <h2>Benchmark Dashboard</h2>
            <p>Filesystem result loading, leaderboard views, breakdowns, and UI structure.</p>
            <strong>Open dashboard docs -&gt;</strong>
          </Link>
        </section>
      </main>
    </Layout>
  );
}
