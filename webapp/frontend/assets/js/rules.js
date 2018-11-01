/* eslint no-unused-vars: 0 */
/* eslint no-undef: 0 */
/* eslint no-alert: 0 */
/* eslint prefer-destructuring: 0 */
/* eslint no-param-reassign: 0 */

const fact = document.querySelector('#fact');
const operator = document.querySelector('#operator');
const value = document.querySelector('#value');
const nodename = document.querySelector('#nodename');
const action = document.querySelector('.add-parameter');
const actionNodes = document.querySelector('.add-node');
const rules = document.querySelector('#rules_lines');
const pinned = document.querySelector('#pinned_nodes');
const commitbar = document.querySelector('body');
const commit = document.querySelector('.commit-changes');
const totalpinned = document.querySelector('#totalpinned');
const loader = document.querySelector('.loader');
const nodesrule = document.getElementsByName('nodesrule');
const alert = document.querySelector('.alert');
const autocompleteNodes = document.querySelector('#autocomplete__nodes');
const postData = {};
const search = {};
search.facts = [];
search.certname = [];

function validate() {
  action.setAttribute('disabled', 'disabled');
  if (fact.value && operator.value && value.value) {
    action.removeAttribute('disabled');
  }
}

function sendFormFacts(e) {
  e.preventDefault();
  const ruleLine = `<tr>
    <td data-label="fact">${fact.value}</td>
    <td data-label="operator" class="align-center">${operator.value}</td>
    <td data-label="value">${value.value}</td>
    <td class="align-center"></td>
    <td class="align-right">
      <a class="link link--danger remove-item">Remove</a>
    </td>
    </tr>`;

  rules.insertAdjacentHTML('beforeend', ruleLine);
  commitbar.classList.add('show-bar');
  commit.removeAttribute('disabled');
  fact.value = '';
  value.value = '';
  action.setAttribute('disabled', 'disabled');
}

function sendFormNodes(e) {
  e.preventDefault();
  const nodeLine = `<tr>
    <td data-label="node" class="align-left"><a href="http://${nodename.value}">${nodename.value}</a></td>
    <td class="align-right">
      <a class="link link--danger remove-item" data-name="${nodename.value}">Unpin</a>
    </td>
    </tr>`;

  search.certname.forEach((node) => {
    if (node.certname === nodename.value) {
      node.active = 'disabled';
    }
  });

  pinned.insertAdjacentHTML('beforeend', nodeLine);
  commitbar.classList.add('show-bar');
  commit.removeAttribute('disabled');
  nodename.value = '';
  actionNodes.setAttribute('disabled', 'disabled');
  totalpinned.textContent = document.querySelectorAll('#pinned_nodes tr').length;
}

function removeItem(e) {
  if (e.target.classList.contains('remove-item')) {
    const name = e.target.getAttribute('data-name');

    commitbar.classList.add('show-bar');
    commit.removeAttribute('disabled');
    e.target.closest('tr').remove();

    search.certname.forEach((node) => {
      if (node.certname === name) {
        node.active = 'enable';
      }
    });

    totalpinned.textContent = document.querySelectorAll('#pinned_nodes tr').length;
  }
}

function commitChanges() {
  this.setAttribute('disabled', 'disabled');
  loader.classList.add('loader--show');

  postData.facts = [];
  rules.childNodes.forEach((ele) => {
    if (ele.nodeType !== 3) {
      const childData = {};
      ele.childNodes.forEach((data) => {
        if (data.nodeType !== 3 && data.hasAttribute('data-label')) {
          childData[data.getAttribute('data-label')] = data.textContent;
        }
      });
      postData.facts.push(childData);
    }
  });

  postData.nodes = [];
  pinned.childNodes.forEach((ele) => {
    if (ele.nodeType !== 3) {
      const childData = {};
      ele.childNodes.forEach((data) => {
        if (data.nodeType !== 3 && data.hasAttribute('data-label')) {
          postData.nodes.push(data.textContent);
        }
      });
    }
  });

  for (let i = 0; i < 2; i += 1) {
    if (nodesrule[i].checked) {
      postData.match_type = nodesrule[i].value;
    }
  }

  axios.put(urlGroup, postData, {
    headers: { 'X-CSRFToken': csrftoken },
  })
    .then((response) => {
      alert.classList.remove('alert--hide');
      alert.classList.add('alert--success');
      alert.textContent = 'Rules successfully updated!';
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

axios.get(urlGroup)
  .then((response) => {
    loader.classList.remove('loader--show');

    nodesrule.forEach((radio) => {
      radio.removeAttribute('checked');
      if (radio.value === response.data.match_type) {
        radio.setAttribute('checked', 'checked');
      }
    });

    const facts = response.data.facts.map(factItem => `
    <tr>
      <td data-label="fact">${factItem.fact}</td>
      <td data-label="operator" class="align-center">${factItem.operator}</td>
      <td data-label="value">${factItem.value}</td>
      <td class="align-center"></td>
      <td class="align-right">
        <a class="link link--danger remove-item">Remove</a>
      </td>
      </tr>
    `).join('');

    rules.insertAdjacentHTML('beforeend', facts);

    const nodes = response.data.nodes.map(nodeItem => `
      <tr>
      <td data-label="node" class="align-left"><a href="http://${nodeItem}">${nodeItem}</a></td>
      <td class="align-right">
      <a class="link link--danger remove-item" data-name="${nodeItem}">Unpin</a>
      </td>
      </tr>
      `).join('');

    totalpinned.textContent = response.data.nodes.length;
    pinned.insertAdjacentHTML('beforeend', nodes);

    axios.get(urlNodes)
      .then((resp) => {
        search.certname = resp.data;
        search.certname.forEach((node) => {
          if (response.data.nodes.includes(node.certname)) {
            node.active = 'disabled';
          } else {
            node.active = 'enable';
          }
        });
      })
      .catch((error) => {
        search.certname = [];
      });
  })
  .catch((error) => {
    alert.classList.remove('alert--hide');
    alert.classList.add('alert--danger');
    alert.textContent = 'A problem ocurred, try again later!';
    loader.classList.remove('loader--show');
  });

axios.get(urlFacts)
  .then((response) => {
    search.facts = response.data;
  })
  .catch((error) => {
    search.facts = [];
  });

loader.classList.add('loader--show');

fact.addEventListener('blur', validate);
fact.addEventListener('change', validate);
fact.addEventListener('keyup', validate);
fact.addEventListener('input', validate);
operator.addEventListener('click', validate);
operator.addEventListener('change', validate);
value.addEventListener('blur', validate);
value.addEventListener('keyup', validate);
action.addEventListener('click', sendFormFacts);
actionNodes.addEventListener('click', sendFormNodes);
rules.addEventListener('click', removeItem);
pinned.addEventListener('click', removeItem);
commit.addEventListener('click', commitChanges);

nodesrule.forEach(radio => radio.addEventListener('change', () => {
  commitbar.classList.add('show-bar');
  commit.removeAttribute('disabled');
}));

autocompleteNodes.addEventListener('click', (e) => {
  if (e.target.className === 'search__item') {
    actionNodes.removeAttribute('disabled');
  }
});
