/* eslint no-undef: 0 */
/* eslint no-param-reassign: 0 */
const group = document.querySelectorAll('.autocomplete__list');
const autocomplete = document.querySelectorAll('.autocomplete__name');
let clicked = false;

function toggleAutocomplete(e) {
  clicked = false;
  const list = this.nextElementSibling;

  const elePosition = e.target.getBoundingClientRect();

  list.style.left = `${elePosition.x}px`;
  list.style.width = `${elePosition.width + 100}px`;
  list.style.top = `${elePosition.y + elePosition.height + window.scrollY}px`;
  list.style.zIndex = '1000';
  list.classList.add('autocomplete__list--show');

  const dataKey = this.getAttribute('data-values');
  const dataName = this.getAttribute('data-name') || 'name';
  const html = search[dataKey].filter(pos => pos.active !== 'disabled')
    .map(pos => `<li title="${pos.name}" class="search__item" data-id="${pos.id}">${pos[dataName]}</li>`);

  if (html.length > 0) {
    list.innerHTML = html.join('');
  } else {
    list.innerHTML = '<li class="nothing-found">Nothing found</li>';
  }
}

function findMatches(wordToMatch, findOut, dataName) {
  return findOut.filter((word) => {
    const regex = new RegExp(wordToMatch, 'gi');
    return word[dataName].match(regex);
  });
}

function getSelected(e) {
  clicked = false;
  let ele = false;
  if (e.target.className === 'search__item') {
    ele = e.target;
  }

  if (e.target.className === 'hl') {
    ele = e.target.parentNode;
  }

  if (ele) {
    ele.closest('.autocomplete').childNodes[1].value = ele.getAttribute('data-id');
    ele.closest('.autocomplete').childNodes[3].value = ele.textContent;
    clicked = true;
  }
}

function displayMatches() {
  clicked = false;
  const dataKey = this.getAttribute('data-values');
  const dataName = this.getAttribute('data-name') || 'name';

  const matchArray = findMatches(this.value, search[dataKey], dataName);
  const html = matchArray.map((pos) => {
    const regex = new RegExp(this.value, 'gi');
    const resultName = pos[dataName].replace(regex, `<span class="hl">${this.value}</span>`);
    if (pos.active !== 'disabled') {
      return `<li class="search__item" data-id="${pos.id}">${resultName}</li>`;
    }
    return '';
  });

  const list = this.nextElementSibling;
  list.innerHTML = html.join('');

  if (html.length === 0) {
    list.innerHTML = '<li class="nothing-found">Nothing found</li>';
  }
}

function closeAutocomplete(e) {
  if (e.target.className !== 'autocomplete__name form-input--text') {
    group.forEach(ulList => ulList.classList.remove('autocomplete__list--show'));
  }
}

function cleanAutocomplete() {
  if (!clicked) {
    this.value = '';
  }
  clicked = false;
}

autocomplete.forEach(input => input.addEventListener('focus', toggleAutocomplete));
autocomplete.forEach(input => input.addEventListener('keyup', displayMatches));
autocomplete.forEach(inputs => inputs.addEventListener('blur', cleanAutocomplete));
document.addEventListener('click', closeAutocomplete);
group.forEach(ulList => ulList.addEventListener('click', getSelected));
