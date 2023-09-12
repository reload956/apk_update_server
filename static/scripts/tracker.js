window.onload = function () {
const toggleCheckbox = document.getElementById('flexCheckDisabled');
const block_select = document.getElementById('block_edit_select');
const block_new = document.getElementById('block_new');
const block_buttons = document.getElementById('block_edit_buttons');
const track_id = document.getElementById('user_track_id');
const select = document.getElementById('user-select')
const user = document.getElementById('user')
const uid = document.getElementById('uid')


toggleCheckbox.addEventListener('change', () => {
if (toggleCheckbox.checked) {
block_select.style.display = 'block';
block_new.style.display = 'none';
block_buttons.style.display = 'block';
} else {
block_select.style.display = 'none';
block_new.style.display = 'block';
block_buttons.style.display = 'none';
}
});

select.addEventListener('change',() => {
if(select.value != 0){
    track_id.value = select.value
    user.value = names[select.value - 1]
    uid.value = ids[select.value - 1]
}
else{
    track_id.innerText = ""
    user.value = ""
    uid.value = ""
}});
}