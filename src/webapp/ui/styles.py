import streamlit as st

CSS = """
<style>
:root {
    --ufc-red: #D20A0A;
    --ufc-red-dark: #A30000;
    --ufc-bg: #FFFFFF;
    --ufc-bg-soft: #F5F5F5;
    --ufc-text: #1A1A1A;
    --ufc-text-soft: #666666;
    --ufc-border: #E0E0E0;
}

[data-testid="stMainBlockContainer"] {
    max-width: none;
    padding-left: 2rem;
    padding-right: 2rem;
}

[data-testid="stSidebar"] {
    background: var(--ufc-bg-soft);
    border-top: 4px solid var(--ufc-red);
}

[data-testid="stSidebarNav"] a:hover {
    color: var(--ufc-red) !important;
}

[data-testid="stHeaderActionElements"] {
    display: none !important;
}

h1 {
    border-bottom: 3px solid var(--ufc-red);
    padding-bottom: 0.5rem;
    font-weight: 800 !important;
    letter-spacing: -0.02em;
}

h2 {
    border-bottom: 2px solid var(--ufc-red);
    padding-bottom: 0.3rem;
    font-weight: 700 !important;
}

h3 {
    color: var(--ufc-red);
    font-weight: 700 !important;
}

[data-testid="stMetric"] {
    background: var(--ufc-bg-soft);
    border-left: 4px solid var(--ufc-red);
    padding: 1rem 1.25rem;
    border-radius: 0.5rem;
}

[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    font-weight: 800 !important;
    color: var(--ufc-text) !important;
}

[data-testid="stMetricLabel"] {
    font-weight: 600 !important;
    text-transform: uppercase;
    font-size: 0.75rem !important;
    letter-spacing: 0.08em;
    color: var(--ufc-text-soft) !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--ufc-border);
    border-radius: 0.5rem;
    overflow: hidden;
}

[data-testid="stSelectbox"] label {
    font-weight: 600 !important;
    text-transform: uppercase;
    font-size: 0.75rem !important;
    letter-spacing: 0.05em;
    color: var(--ufc-text-soft) !important;
}

[data-testid="stExpander"] summary {
    font-weight: 600;
}

.ufc-nav-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-top: 0.5rem;
}

.ufc-nav-card {
    display: block;
    background: var(--ufc-bg-soft);
    border: 1px solid var(--ufc-border);
    border-radius: 0.5rem;
    padding: 1.5rem;
    text-align: center;
    transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
    text-decoration: none !important;
    color: inherit !important;
    cursor: pointer;
}

.ufc-nav-card:hover {
    border-color: var(--ufc-red);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(210, 10, 10, 0.15);
}

.ufc-nav-card h3 {
    color: var(--ufc-red);
    margin: 0.25rem 0 0.5rem 0;
    border-bottom: none;
}

.ufc-nav-card p {
    color: var(--ufc-text-soft);
    font-size: 0.85rem;
    margin: 0;
}

.ufc-hero {
    font-size: 3.25rem !important;
    font-weight: 900 !important;
    letter-spacing: -0.03em;
    border-bottom: none !important;
    margin-bottom: 0.25rem !important;
    padding-bottom: 0 !important;
}

.ufc-hero-accent {
    color: var(--ufc-red);
}

.ufc-fighter-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
}

.ufc-fighter-card-link {
    display: block;
    text-decoration: none !important;
    color: inherit !important;
    cursor: pointer;
    height: 100%;
}

.ufc-fighter-card {
    background: var(--ufc-bg-soft);
    border: 1px solid var(--ufc-border);
    border-radius: 0.5rem;
    overflow: hidden;
    transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
    cursor: pointer;
    height: 100%;
}

.ufc-fighter-card-link:hover .ufc-fighter-card {
    border-color: var(--ufc-red);
    transform: translateY(-3px);
    box-shadow: 0 0 0 1px rgba(210, 10, 10, 0.16), 0 10px 22px rgba(210, 10, 10, 0.14);
}

.ufc-fighter-card__photo {
    width: 100%;
    height: 168px;
    object-fit: cover;
    display: block;
    background: var(--ufc-border);
}

.ufc-fighter-card__placeholder {
    width: 100%;
    height: 168px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--ufc-border);
    color: var(--ufc-text-soft);
    font-size: 2.5rem;
    font-weight: 800;
    letter-spacing: 0.05em;
}

.ufc-fighter-card__body {
    padding: 0.85rem 0.85rem 0.9rem 0.85rem;
}

.ufc-fighter-card__name {
    font-weight: 700;
    font-size: 0.9rem;
    color: var(--ufc-text);
    margin: 0 0 0.25rem 0;
    line-height: 1.25;
    min-height: 2.25rem;
}

.ufc-fighter-card__record {
    color: var(--ufc-red);
    font-weight: 800;
    font-size: 1.05rem;
    margin: 0 0 0.45rem 0;
}

.ufc-fighter-card__division {
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--ufc-text);
    margin: 0 0 0.5rem 0;
}

.ufc-fighter-card__meta {
    font-size: 0.66rem;
    color: var(--ufc-text-soft);
    line-height: 1.5;
    border-top: 1px solid var(--ufc-border);
    padding-top: 0.45rem;
    margin-top: 0.25rem;
}

@media (max-width: 900px) {
    [data-testid="stMainBlockContainer"] {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .ufc-fighter-grid {
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 0.75rem;
    }

    .ufc-fighter-card__photo,
    .ufc-fighter-card__placeholder {
        height: 156px;
    }

    .ufc-profile-photo-shell,
    .ufc-profile-photo,
    .ufc-profile-photo-placeholder {
        height: 22rem;
        min-height: 0;
    }
}

.ufc-hero-tagline {
    color: var(--ufc-text-soft);
    font-size: 1.1rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    font-weight: 600;
    margin-bottom: 2rem;
}

.ufc-profile-photo-shell {
    position: relative;
    height: clamp(15.5rem, 29vw, 20rem);
    border-radius: 1.25rem;
    overflow: hidden;
    background:
        radial-gradient(circle at top right, rgba(210, 10, 10, 0.28), transparent 38%),
        linear-gradient(160deg, #181818 0%, #2A2A2A 100%);
    border: 1px solid rgba(26, 26, 26, 0.08);
}

.ufc-profile-photo {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center top;
    display: block;
}

.ufc-profile-photo-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #FFFFFF;
    font-size: clamp(4rem, 7vw, 6rem);
    font-weight: 900;
    letter-spacing: 0.08em;
}

.ufc-profile-hero-copy {
    padding: 0.35rem 0.25rem 0.35rem 0;
}

.ufc-profile-eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.16em;
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--ufc-red);
    margin-bottom: 0.9rem;
}

.ufc-profile-name {
    font-size: clamp(2.5rem, 5vw, 4.5rem) !important;
    line-height: 0.95;
    font-weight: 900 !important;
    letter-spacing: -0.04em;
    border-bottom: none !important;
    padding-bottom: 0 !important;
    margin-bottom: 0.4rem !important;
}

.ufc-profile-nickname {
    color: var(--ufc-text-soft);
    font-size: 1rem;
    margin-bottom: 1.4rem;
}

.ufc-profile-summary {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-top: 1rem;
}

.ufc-profile-summary-item {
    display: inline-flex;
    align-items: center;
    min-height: 2.5rem;
    padding: 0.6rem 0.95rem;
    border-radius: 999px;
    background: rgba(26, 26, 26, 0.04);
    border: 1px solid rgba(26, 26, 26, 0.08);
    font-weight: 600;
    color: var(--ufc-text);
}

.ufc-profile-meta-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.9rem;
    margin: 0.5rem 0 1rem 0;
}

.ufc-profile-meta-item {
    padding: 1rem 1.05rem;
    border-radius: 1rem;
    background: linear-gradient(180deg, #FAFAFA 0%, #F4F4F4 100%);
    border: 1px solid rgba(26, 26, 26, 0.06);
}

.ufc-profile-meta-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--ufc-text-soft);
    font-weight: 700;
    margin-bottom: 0.45rem;
}

.ufc-profile-meta-value {
    font-size: 1rem;
    font-weight: 700;
    color: var(--ufc-text);
}

.ufc-profile-fights {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    margin-top: 0.5rem;
}

.ufc-profile-fight-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.05rem;
    border-radius: 1rem;
    background: #FFFFFF;
    border: 1px solid rgba(26, 26, 26, 0.08);
}

.ufc-profile-fight-main {
    display: flex;
    align-items: flex-start;
    gap: 0.9rem;
    min-width: 0;
}

.ufc-profile-fight-result {
    min-width: 4.75rem;
    text-align: center;
    padding: 0.45rem 0.65rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.ufc-profile-fight-result.win {
    background: rgba(23, 132, 75, 0.12);
    color: #167246;
}

.ufc-profile-fight-result.loss {
    background: rgba(210, 10, 10, 0.12);
    color: var(--ufc-red-dark);
}

.ufc-profile-fight-result.draw {
    background: rgba(26, 26, 26, 0.08);
    color: var(--ufc-text);
}

.ufc-profile-fight-copy {
    min-width: 0;
}

.ufc-profile-fight-opponent {
    font-size: 1rem;
    font-weight: 800;
    color: var(--ufc-text);
    margin-bottom: 0.2rem;
}

.ufc-profile-fight-event,
.ufc-profile-fight-method {
    color: var(--ufc-text-soft);
    font-size: 0.9rem;
}

.ufc-profile-fight-tags {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 0.5rem;
}

.ufc-profile-tag {
    display: inline-flex;
    align-items: center;
    padding: 0.38rem 0.65rem;
    border-radius: 999px;
    background: rgba(210, 10, 10, 0.08);
    color: var(--ufc-red-dark);
    font-size: 0.78rem;
    font-weight: 700;
}

.ufc-profile-insights {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 0.9rem;
    margin-top: 0.5rem;
}

.ufc-profile-insight {
    padding: 1.1rem;
    border-radius: 1rem;
    background:
        radial-gradient(circle at top right, rgba(210, 10, 10, 0.12), transparent 40%),
        linear-gradient(180deg, #FFFFFF 0%, #F7F7F7 100%);
    border: 1px solid rgba(26, 26, 26, 0.08);
}

.ufc-profile-insight-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--ufc-text-soft);
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.ufc-profile-insight-value {
    font-size: 1.5rem;
    font-weight: 900;
    letter-spacing: -0.03em;
    color: var(--ufc-text);
    margin-bottom: 0.35rem;
}

.ufc-profile-insight-detail {
    color: var(--ufc-text-soft);
    font-size: 0.9rem;
}

.ufc-profile-empty {
    padding: 1rem 0;
    color: var(--ufc-text-soft);
}

@media (max-width: 900px) {
    .ufc-profile-fight-row {
        flex-direction: column;
        align-items: flex-start;
    }

    .ufc-profile-fight-tags {
        justify-content: flex-start;
    }
}
</style>
"""


def inject_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
