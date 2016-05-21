var content_type_input = document.getElementById('content_type_input')
var file_input = document.getElementById('file_input');

if (file_input) {
  file_input.addEventListener('change', function(event) {
    content_type_input.value = file_input.files[0].type;
  });
}
