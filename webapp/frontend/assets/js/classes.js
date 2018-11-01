/* eslint no-unused-vars: 0 */
/* eslint no-undef: 0 */
/* eslint no-alert: 0 */
/* eslint prefer-destructuring: 0 */
/* eslint no-param-reassign: 0 */

const addClass = document.querySelector('.add-classes');
const className = document.querySelector('#class_name');
const classId = document.querySelector('#class_id');
const container = document.querySelector('#classes_container');
const commitbar = document.querySelector('body');
const commit = document.querySelector('.commit-changes');
const loader = document.querySelector('.loader');
const alert = document.querySelector('.alert');
const autocomplete = document.querySelector('.autocomplete__list');
const postData = {};
const search = {};

let inputs;
let selects;
let indice = 0;

function validateValue() {
  const blockValidate = this.closest('tr');
  const inputParam = blockValidate.querySelector('.parameter').value;
  const addParam = this.closest('tr').querySelector('.add-parameter');
  addParam.setAttribute('disabled', 'disabled');

  if (!inputParam) {
    return;
  }

  let inputValue = blockValidate.querySelector('.value').value;
  const checkTypeByClass = blockValidate.querySelector('.value').classList;

  if (checkTypeByClass.contains('float')) {
    inputValue = inputValue.replace(/[^0-9.]/g, '');
    blockValidate.querySelector('.value').value = inputValue.replace(/\..*/, c => `.${c.replace(/\./g, () => '')}`);
  }

  if (checkTypeByClass.contains('integer')) {
    inputValue = inputValue.replace(/[^0-9]/g, '');
    blockValidate.querySelector('.value').value = inputValue;
  }

  if (inputValue) {
    addParam.removeAttribute('disabled');
  }
}

function htmlOptions(params, used = []) {
  return params.map((param) => {
    const check = used.includes(param.name) || false;
    const defaultValues = param.values.isArray ? param.values.join(',') : param.values;
    return `<option ${(check) ? 'disabled="disabled"' : ''} data-type="${param.type}" data-values="${defaultValues}" data-default="${param.default}">${param.name}</option>`;
  }).join('');
}

function checkEmptyOrZero(value) {
  return (value !== 0 && value !== '0' && value !== '') ? value : '';
}

function changeInput() {
  const getContainer = this.closest('tr').querySelector('.input-container');

  if (!this.value) {
    getContainer.innerHTML = '';
    validateValue.apply(this);
    return;
  }

  const selected = this.options[this.selectedIndex];
  const sPlaceholder = selected.dataset.type;
  const sType = sPlaceholder.toUpperCase();
  const sValues = selected.dataset.values.split(',');
  const sDefault = checkEmptyOrZero(selected.dataset.default);

  let html = '';

  switch (sType) {
    case 'HASH':
    case 'ARRAY':
      html = `<textarea placeholder="${sPlaceholder}" class="value form-input--text">${sDefault}</textarea>`;
      break;
    case 'BOOLEAN':
    case 'ENUM':
      html = `<select class="value form-input--select">${sValues.map((label) => {
        const checkDefault = label === sDefault;
        return `<option ${checkDefault ? 'selected="selected"' : ''}>${label}</option>`;
      }).join('')}</select>`;
      break;
    case 'INTEGER':
      html = `<input placeholder="${sPlaceholder}" type="number" step="1" min="0" value="${sDefault}" class="value integer form-input--text">`;
      break;
    case 'FLOAT':
      html = `<input placeholder="${sPlaceholder}" type="text" value="${sDefault}" class="value float form-input--text">`;
      break;
    default:
      html = `<input placeholder="${sPlaceholder}" type="text" value="${sDefault}" class="value form-input--text">`;
  }

  getContainer.innerHTML = `${html}<span class="type">${sPlaceholder}</span>`;

  const newInput = this.closest('tr').querySelector('.value');
  newInput.addEventListener('keyup', validateValue);
  newInput.addEventListener('blur', validateValue);

  validateValue.apply(this);
}

function addParameter(val) {
  const parentClass = document.querySelector(val);
  const parameter = parentClass.querySelector('.parameter');
  const value = parentClass.querySelector('.value');
  const button = parentClass.querySelector('.add-parameter');
  const tbody = parentClass.querySelector('tbody');

  parameter.querySelectorAll('option').forEach((option) => {
    if (option.textContent === parameter.value) {
      option.setAttribute('disabled', 'disabled');
    }
  });

  const paramInfo = `
  <tr>
    <td data-info="parameter">${parameter.value}</td>
    <td class="equal">=</td>
    <td data-info="value">${value.value}</td>
    <td class="align-right">
      <a class="link link--danger remove-item">Remove</a>
    </td>
  </tr>`;

  tbody.insertAdjacentHTML('beforeend', paramInfo);
  commitbar.classList.add('show-bar');
  commit.removeAttribute('disabled');
  parameter.value = '';
  value.closest('.input-container').innerHTML = '';
  button.setAttribute('disabled', 'disabled');
}

function generateClassBlock(blockIndex, blockId, blockName, blockValues, blockUsed = [], blockData = '') {
  return `
    <div class="class-block" id="group_${blockIndex}" data-id="${blockId}">
      <h3>Class: <span>${blockName}</span></h3>
      <table class="class-block__table">
        <thead>
        <tr>
          <th class="th-1">Parameter</th>
          <th class="th-2"></th>
          <th class="th-3">Value</th>
          <th class="th-4 align-right"><a class="link link--danger remove-class" data-name="${blockName}">Remove Class</a></th>
        </tr>
        <tr>
          <td>
          <span class="form-input--select">
            <select class="parameter">
              <option value="">Select an paramenter</option>
              ${htmlOptions(blockValues, blockUsed)}
            </select>
          </span>
          </td>
          <td class="equal">=</td>
          <td>
            <span class="form-input input-container">
            </span>
          </td>
          <td class="align-right">
            <button class="form-input--submit add-parameter" onclick="addParameter('#group_${blockIndex}');" disabled="disabled">Add Parameter</button>
          </td>
        </tr>
        </thead>
        <tbody>
        ${blockData}
        </tbody>
      </table>
    </div>
    `;
}

function addClasses(e) {
  e.preventDefault();
  axios.get(`${urlParameters}${classId.value}`)
    .then((response) => {
      search.classes.forEach((sitem) => {
        if (sitem.name === className.value) {
          sitem.active = 'disabled';
        }
      });

      indice += 1;
      container.insertAdjacentHTML('beforeend', generateClassBlock(indice, classId.value, className.value, response.data));
      commitbar.classList.add('show-bar');
      commit.removeAttribute('disabled');
      className.value = '';
      addClass.setAttribute('disabled', 'disabled');

      inputs = document.querySelectorAll('.value');
      inputs.forEach((input) => {
        input.addEventListener('keyup', validateValue);
        input.addEventListener('blur', validateValue);
      });

      selects = document.querySelectorAll('.parameter');
      selects.forEach((select) => {
        select.addEventListener('change', changeInput);
      });
    })
    .catch((error) => {
      alert('A problem ocurred, try again later');
    });
}

function removeItem(e) {
  if (e.target.classList.contains('remove-class')) {
    const name = e.target.getAttribute('data-name');

    search.classes.forEach((sitem) => {
      if (sitem.name === name) {
        sitem.active = 'enable';
      }
    });

    commitbar.classList.add('show-bar');
    commit.removeAttribute('disabled');
    e.target.closest('.class-block').remove();
  }
}

function removeParameter(e) {
  if (e.target.classList.contains('remove-item')) {
    const allowParameter = e.target.closest('tr').querySelector('td[data-info="parameter"]').textContent;
    const AddOptionsSelect = e.target.closest('.class-block').querySelector('.parameter').querySelectorAll('option');

    AddOptionsSelect.forEach((option) => {
      if (option.textContent === allowParameter) {
        option.removeAttribute('disabled');
      }
    });

    commitbar.classList.add('show-bar');
    commit.removeAttribute('disabled');
    e.target.closest('tr').remove();
  }
}

function commitChanges() {
  this.setAttribute('disabled', 'disabled');

  const blocks = document.querySelectorAll('.class-block');
  postData.classes = [];

  blocks.forEach((block) => {
    const title = block.querySelector('h3 span').textContent;
    const body = block.querySelectorAll('tbody tr');

    const parameters = [];
    body.forEach((data) => {
      parameters.push({
        value: data.querySelector('td[data-info="value"]').textContent,
        raw_value: data.querySelector('td[data-info="value"]').textContent,
        parameter: data.querySelector('td[data-info="parameter"]').textContent,
      });
    });

    postData.classes.push({
      puppet_class: title,
      parameters,
    });
  });

  loader.classList.add('loader--show');

  axios.put(urlGroup, postData, {
    headers: { 'X-CSRFToken': csrftoken },
  })
    .then((response) => {
      alert.classList.remove('alert--hide');
      alert.classList.add('alert--success');
      alert.textContent = 'Classes successfully updated!';
      loader.classList.remove('loader--show');
      commitbar.classList.remove('show-bar');
    })
    .catch((error) => {
      // error.response.data
      alert.classList.remove('alert--hide');
      alert.classList.add('alert--danger');
      alert.textContent = 'A problem ocurred, try again later';
      loader.classList.remove('loader--show');
    });
}

function loadClasses() {
  axios.get(urlClasses)
    .then((response) => {
      search.classes = response.data;
      search.classes.forEach((sitem) => {
        sitem.active = 'enable';
      });
    })
    .then(() => {
      axios.get(urlGroup)
        .then((response) => {
          container.innerHTML = '';

          const classes = response.data.classes;
          if (classes) {
            classes.forEach((data) => {
              search.classes.forEach((sitem) => {
                if (sitem.name === data.puppet_class) {
                  sitem.active = 'disabled';
                }
              });

              const id = search.classes.filter(val => val.name === data.puppet_class);
              if (id[0]) {
                axios.get(`${urlParameters}${id[0].id}`)
                  .then((params) => {
                    const used = [];
                    const htmlParameters = data.parameters.map((param) => {
                      used.push(param.parameter);

                      let value = param.value;
                      if (typeof param.value === 'object') {
                        value = `<pre>${JSON.stringify(param.value, null, 2)}</pre>`;
                      }

                      return `<tr>
                        <td data-info="parameter">${param.parameter}</td>
                        <td class="equal">=</td>
                        <td data-info="value">${value}</td>
                        <td class="align-right">
                          <a class="link link--danger remove-item">Remove</a>
                        </td>
                      </tr>`;
                    }).join('');

                    indice += 1;
                    container.insertAdjacentHTML('beforeend', generateClassBlock(indice, id.id, data.puppet_class, params.data, used, htmlParameters));

                    inputs = document.querySelectorAll('.value');
                    inputs.forEach((input) => {
                      input.addEventListener('keyup', validateValue);
                      input.addEventListener('blur', validateValue);
                    });

                    selects = document.querySelectorAll('.parameter');
                    selects.forEach((select) => {
                      select.addEventListener('change', changeInput);
                    });
                  })
                  .catch((error) => {
                    alert.classList.remove('alert--hide');
                    alert.classList.add('alert--danger');
                    alert.textContent = 'A problem ocurred, try again later!';
                  });
              }
            });
          }
        })
        .then(() => {
          loader.classList.remove('loader--show');
        })
        .catch((error) => {
          alert.classList.remove('alert--hide');
          alert.classList.add('alert--danger');
          alert.textContent = 'A problem ocurred, try again later!';
          loader.classList.remove('loader--show');
        });
    })
    .catch((error) => {
      search.classes = [];
    });
}

loadClasses();

loader.classList.add('loader--show');

addClass.addEventListener('click', addClasses);
container.addEventListener('click', removeItem);
container.addEventListener('click', removeParameter);
commit.addEventListener('click', commitChanges);

className.addEventListener('keyup', () => {
  addClass.setAttribute('disabled', 'disabled');
});

autocomplete.addEventListener('click', (e) => {
  if (e.target.className === 'search__item') {
    addClass.removeAttribute('disabled');
  }
});
