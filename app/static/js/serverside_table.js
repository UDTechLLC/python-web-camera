/*jslint browser: true*/
/*global $*/
$(document).ready(function () {
    // Edit

    $('#serverside_table').on('click', 'button.editor_edit', function (e) {
        e.preventDefault();
        var id = tablePackages.row($(this).closest('tr')).data().id;
        document.location.href = "/edit-package/" + id;
    } );

    var idDelete;
    var rowTable;
    // Delete a record
    $('#serverside_table').on('click', 'button.editor_remove', function (e) {
        e.preventDefault();
        idDelete = tablePackages.row($(this).closest('tr')).data().id;
    } );

    $('#modalDelete').on('click', 'button.btn-primary', function (e) {
        console.log('/delete-package/' + idDelete);
        $.ajax({
            type: 'DELETE',
            url: '/delete-package/' + idDelete,
            contentType: "application/json",
            dataType: 'json',
            data: [],
        }).done(function( msg ) {
            if( msg == 'success' ){
                $('#modalDelete').modal('hide');
                tablePackages.ajax.url( '/table_package_ajax' ).load();
            }
        });
    });
  if($('.btn-train').hasClass('active')){
    contentActionColumn = '<button type="button" class="editor_edit">Редактировать</a><button type="button" data-toggle="modal" class="editor_remove" data-target="#modalDelete">Удалить</button>';
  }else{
    contentActionColumn = 'Идет тренировка';
  }
  var tablePackages = $('#serverside_table').DataTable({
    "language": {
        "url": "/static/js/russian.json"
    },
    "createdRow": function( row, data, dataIndex){
        console.log(data)
        console.log(data["train_status"])
        if( data["train_status"] !=  1){
            $(row).addClass('redClass');
        }
    },
    bProcessing: true,
    bServerSide: true,
    sPaginationType: "full_numbers",
    lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
    bjQueryUI: true,
    sAjaxSource: '/table_package_ajax',
    columns: [
      {"data": "id"},
      {"data": "name"},
      {"data": "manufacturer"},
      {"data": "barcode"},
      {"data": "Release form"},
      {"data": "amount"},
      {"data": "Content mg"},
      {"data": "Volume, ml"},
      {
        data: null,
        defaultContent: contentActionColumn
      },
      {"data": "train_status"}
    ],
  });
});
