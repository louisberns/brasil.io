var dt;

jQuery(document).ready(function() {
  dt = jQuery('.mdl-data-table').DataTable({
    "autoWidth": false,
    "columns": [
      { "width": "20%" },
      { "width": "20%" },
      { "width": "16%" },
      { "width": "11%" },
      { "width": "11%" },
      { "width": "11%" },
      { "width": "11%" }
    ],
    "scrollY":        "650px",
    "scrollCollapse": true,
    "paging":         false,
    "searching":      true,
    "bInfo":          false,
    "order": [3, "desc"],
    "language": {
      search: "Buscar:",
      searchPlaceholder: "Digite seu município aqui",
    },
  });
});
