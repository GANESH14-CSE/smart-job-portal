document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss alerts after 5 seconds
  document.querySelectorAll('.alert.alert-dismissible').forEach(el => {
    setTimeout(() => { try { bootstrap.Alert.getOrCreateInstance(el).close(); } catch(e){} }, 5000);
  });
  // Animate progress bars
  document.querySelectorAll('.progress-bar').forEach(bar => {
    const w = bar.style.width;
    bar.style.width = '0%';
    bar.style.transition = 'width 1s ease';
    requestAnimationFrame(() => requestAnimationFrame(() => { bar.style.width = w; }));
  });
});
