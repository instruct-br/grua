/* eslint no-undef: 0 */
/* eslint no-unused-vars: 0 */
const input = document.querySelector('input[name=tags]');
const masterZoneSelect = document.getElementById('id_master_zone');
const environmentSelect = document.getElementById('id_environment');

const tagify = new Tagify(input, {
  callbacks: {
    add: function onAddTag(event) {
      input.value = input.value.replace(/"/g, '');
    },
  },
});

const defaultPlaceholder = function setDefaultSelects() {
  const label = 'Select a Master zone';
  masterZoneSelect.firstElementChild.textContent = label;
  environmentSelect.innerHTML = `<option>${label}</option>`;
  return false;
};

const loadEnvironments = function loadEnvironmentSelect(e) {
  if (!this.value) {
    return defaultPlaceholder();
  }

  axios.get('environments-options/', {
    params: {
      master_zone: this.value,
    },
  })
    .then((response) => {
      environmentSelect.innerHTML = response.data;
    })
    .catch(defaultPlaceholder);
  return true;
};

if (masterZoneSelect && environmentSelect) {
  defaultPlaceholder();
  masterZoneSelect.addEventListener('change', loadEnvironments);
}
