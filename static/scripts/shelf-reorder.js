htmx.onLoad(function(content) {
  content.querySelectorAll(".sortable").forEach(function(el) {
    new Sortable(el, {
      handle: ".drag-handle",
      animation: 150,
      ghostClass: "sortable-ghost",
    });
  });
});

document.body.addEventListener("htmx:responseError", function() {
  window.location.reload();
});
