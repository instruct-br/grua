const navTrigger = document.querySelectorAll('.nav-toggle');
const body = document.querySelector('body');

navTrigger.forEach(button => button.addEventListener('click', () => {
  body.classList.toggle('nav--opened');
}));

document.addEventListener('click', (e) => {
  const hasAlert = document.querySelector('.alert');
  if (e.target.classList.contains('alert--danger') || e.target.classList.contains('alert--success')) {
    hasAlert.classList.add('alert--hide');
    hasAlert.classList.remove('alert--success');
    hasAlert.classList.remove('alert--danger');
  }
});
