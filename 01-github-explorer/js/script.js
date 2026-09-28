const form = document.querySelector('#search-form');
const usernameInput = document.querySelector('#username');
const formMessage = document.querySelector('#form-message');
const status = document.querySelector('#status');
const grid = document.querySelector('#repository-grid');
const controls = document.querySelector('#controls');
const languageFilter = document.querySelector('#language-filter');
const sortBy = document.querySelector('#sort-by');
const resultSummary = document.querySelector('#result-summary');

let repositories = [];
let activeUsername = '';

const savedUsername = localStorage.getItem('githubExplorerLastUsername');
if (savedUsername) usernameInput.value = savedUsername;

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const username = usernameInput.value.trim();

  if (!username) {
    formMessage.textContent = 'Please enter a GitHub username before searching.';
    usernameInput.focus();
    return;
  }
  if (!/^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$|^[a-zA-Z0-9]$/.test(username)) {
    formMessage.textContent = 'Enter a valid GitHub username.';
    usernameInput.focus();
    return;
  }

  formMessage.textContent = '';
  await searchRepositories(username);
});

languageFilter.addEventListener('change', renderRepositories);
sortBy.addEventListener('change', renderRepositories);

async function searchRepositories(username) {
  activeUsername = username;
  repositories = [];
  controls.hidden = true;
  grid.innerHTML = '';
  resultSummary.textContent = `Looking up @${username}…`;
  setStatus('Loading repositories...', 'loading');

  try {
    const response = await fetch(`https://api.github.com/users/${encodeURIComponent(username)}/repos?per_page=150&sort=updated`);
    if (response.status === 404) throw new Error('User not found. Check the username and try again.');
    if (!response.ok) throw new Error('Unable to load repositories right now. Please try again later.');

    repositories = await response.json();
    localStorage.setItem('githubExplorerLastUsername', username);
    populateLanguages(repositories);

    if (repositories.length === 0) {
      setStatus(`${username} does not have any public repositories.`, 'error');
      resultSummary.textContent = 'No public repositories found.';
      return;
    }

    status.textContent = '';
    status.className = 'status';
    controls.hidden = false;
    resultSummary.textContent = `${repositories.length} public ${repositories.length === 1 ? 'repository' : 'repositories'} for @${username}`;
    renderRepositories();
  } catch (error) {
    resultSummary.textContent = 'Search could not be completed.';
    setStatus(error.message || 'Something went wrong. Please try again.', 'error');
  }
}

function populateLanguages(items) {
  const languages = [...new Set(items.map((repo) => repo.language || 'Other'))].sort((a, b) => a.localeCompare(b));
  languageFilter.innerHTML = '<option value="all">All languages</option>';
  languages.forEach((language) => {
    const option = document.createElement('option');
    option.value = language;
    option.textContent = language;
    languageFilter.append(option);
  });
}

function renderRepositories() {
  const selectedLanguage = languageFilter.value;
  const sorted = repositories
    .filter((repo) => selectedLanguage === 'all' || (repo.language || 'Other') === selectedLanguage)
    .sort((a, b) => {
      if (sortBy.value === 'stars-desc') return b.stargazers_count - a.stargazers_count || a.name.localeCompare(b.name);
      if (sortBy.value === 'stars-asc') return a.stargazers_count - b.stargazers_count || a.name.localeCompare(b.name);
      return a.name.localeCompare(b.name);
    });

  grid.innerHTML = '';
  if (!sorted.length) {
    grid.innerHTML = '<p class="empty">No repositories match this language filter.</p>';
    return;
  }

  const fragment = document.createDocumentFragment();
  sorted.forEach((repo) => fragment.append(createRepositoryCard(repo)));
  grid.append(fragment);
}

function createRepositoryCard(repo) {
  const card = document.createElement('article');
  card.className = 'repo-card';

  const title = document.createElement('h3');
  const link = document.createElement('a');
  link.href = repo.html_url;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  link.textContent = repo.name;
  title.append(link);

  const description = document.createElement('p');
  description.className = 'repo-description';
  description.textContent = repo.description || 'No description provided.';

  const meta = document.createElement('div');
  meta.className = 'repo-meta';
  const language = document.createElement('span');
  language.innerHTML = '<i class="language-dot" aria-hidden="true"></i>';
  language.append(document.createTextNode(repo.language || 'Other'));
  const stars = document.createElement('span');
  stars.textContent = `★ ${repo.stargazers_count.toLocaleString()}`;
  meta.append(language, stars);

  card.append(title, description, meta);
  return card;
}

function setStatus(message, type) {
  status.textContent = message;
  status.className = `status ${type}`;
}
