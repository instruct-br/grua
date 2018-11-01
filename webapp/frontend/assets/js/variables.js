/* eslint no-unused-vars: 0 */
/* eslint no-undef: 0 */
/* eslint no-alert: 0 */
/* eslint prefer-destructuring: 0 */
/* eslint no-param-reassign: 0 */

const addVariable = document.querySelector('.add-variable');
const key = document.querySelector('#key');
const value = document.querySelector('#value');
const commitbar = document.querySelector('body');
const commit = document.querySelector('.commit-changes');
const loader = document.querySelector('.loader');
const alert = document.querySelector('.alert');
const variables = document.querySelector('#variables_lines');
const postData = {};

function validate() {
  addVariable.setAttribute('disabled', 'disabled');
  if (key.value && value.value) {
    addVariable.removeAttribute('disabled');
  }
}

function insertVariables(e) {
  e.preventDefault();
  const varLine = `<tr>
    <td data-label="key">${key.value}</td>
    <td data-label="operator" class="align-center">=</td>
    <td data-label="value">${value.value}</td>
    <td class="align-right">
      <a class="link link--danger remove-item">Remove</a>
    </td>
    </tr>`;

  variables.insertAdjacentHTML('beforeend', varLine);
  commitbar.classList.add('show-bar');
  commit.removeAttribute('disabled');
  key.value = '';
  value.value = '';
  addVariable.setAttribute('disabled', 'disabled');
}

function commitChanges() {
  this.setAttribute('disabled', 'disabled');

  postData.data = {};

  variables.querySelectorAll('tr').forEach((tr) => {
    const vKey = tr.querySelector('td[data-label="key"]').textContent;
    const vValue = tr.querySelector('td[data-label="value"]').textContent;
    postData.data[vKey] = vValue;
  });

  loader.classList.add('loader--show');

  axios.put(urlVariables, postData, {
    headers: { 'X-CSRFToken': csrftoken },
  })
    .then((response) => {
      alert.classList.remove('alert--hide');
      alert.classList.add('alert--success');
      alert.textContent = 'Variables successfully updated!';
      loader.classList.remove('loader--show');
      commitbar.classList.remove('show-bar');
    })
    .catch((error) => {
      alert.classList.remove('alert--hide');
      alert.classList.add('alert--danger');
      alert.textContent = Object.values(error.response.data).join('<br>');
      loader.classList.remove('loader--show');
    });
}

function removeItem(e) {
  if (e.target.classList.contains('remove-item')) {
    commitbar.classList.add('show-bar');
    commit.removeAttribute('disabled');
    e.target.closest('tr').remove();
  }
}

axios.get(urlVariables)
  .then((response) => {
    loader.classList.remove('loader--show');
    const list = response.data.data;
    if (!list) {
      return;
    }

    Object.entries(list).forEach((val) => {
      const varLine = `<tr>
        <td data-label="key">${val[0]}</td>
        <td data-label="operator" class="align-center">=</td>
        <td data-label="value">${val[1]}</td>
        <td class="align-right">
          <a class="link link--danger remove-item">Remove</a>
        </td>
        </tr>`;

      variables.insertAdjacentHTML('beforeend', varLine);
    });
  })
  .catch((error) => {
    alert.classList.remove('alert--hide');
    alert.classList.add('alert--danger');
    alert.textContent = 'A problem ocurred, try again later!';
    loader.classList.remove('loader--show');
  });

loader.classList.add('loader--show');

key.addEventListener('blur', validate);
key.addEventListener('keyup', validate);
value.addEventListener('blur', validate);
value.addEventListener('keyup', validate);
addVariable.addEventListener('click', insertVariables);
variables.addEventListener('click', removeItem);
commit.addEventListener('click', commitChanges);
