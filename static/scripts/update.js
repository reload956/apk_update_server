window.onload = function () {

const toggleCheckbox = document.getElementById('flexCheckDisabled');
const block_select = document.getElementById('block_update_select');
const block_name = document.getElementById('block_name_select');
const version = document.getElementById('version');
const description = document.getElementById('description');
const select = document.getElementById('manifest-select')


toggleCheckbox.addEventListener('change', () => {
if (toggleCheckbox.checked) {
block_select.style.display = 'block';
block_name.style.display = 'none';
} else {
block_select.style.display = 'none';
block_name.style.display = 'block';
version.value= ""
description.placeholder= ""
description.value= ""
}
});

select.addEventListener('change',() => {
if(select.value != ""){
    jQuery.getJSON("/manifests/" + select.value, function (data) {
    version.value = data.versionCode + 1;
    description.placeholder =  "Предидущая: " + data.updateMessage;
    })
}
else{

}});
}