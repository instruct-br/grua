/* eslint no-unused-vars: 0 */
/* eslint no-undef: 0 */

const syncButton = document.querySelector('.sync-masterzone');
const alert = document.querySelector('.alert');

function syncAction(e) {
  const masterId = this.dataset.masterzone;
  const masterLabel = this.dataset.label;

  axios.post(urlSync, { master_id: masterId }, { headers: { 'X-CSRFToken': csrftoken } })
    .then((response) => {
      alert.className = 'alert alert--success';
      alert.textContent = `Data sync started in Master Zone: ${masterLabel}`;
    })
    .catch((error) => {
      alert.className = 'alert alert--danger';
      alert.textContent = `A problem ocurred starting sync in Master Zone: ${masterLabel}`;
    });
}

syncButton.addEventListener('click', syncAction);
