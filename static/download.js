async function get_info() {
    let response = await fetch('http://127.0.0.1:5000/get_download_info', {
        method: 'POST'
    });
    let json= await response.json();
    Object.keys(json).forEach(function(key) {
        if (Object.keys(downloads_array).includes(key)) {
            bar = document.querySelector(`#val1_bar_${downloads_array[key].num}`);
            bar.value = json[key][1];

            sp = document.querySelector(`#val1_2text_${downloads_array[key].num}`);
            sp.textContent = `${json[key][0]}/${json[key][1]}`;

        } else {
            if (json[key][1]) {
                downloads_array[key] = {'num': Object.keys(downloads_array).length + 1, 'cur': json[key][1], 'max': json[key][0]}
                row = document.querySelector('#row');
                clone = row.content.cloneNode(true);

                d = clone.querySelector('div');
                d.id = `window_${downloads_array[key].num}`

                sp = clone.querySelectorAll('span')[0];
                sp.id = `val1_text_${downloads_array[key].num}`;
                sp.textContent = key;

                bar = clone.querySelector('progress');
                bar.id = `val1_bar_${downloads_array[key].num}`
                bar.max = json[key][0];
                bar.value = json[key][1];

                sp2 = clone.querySelectorAll('span')[1];
                sp2.id = `val1_2text_${downloads_array[key].num}`;
                sp2.textContent = `${json[key][0]}/${json[key][1]}`;

                cont = document.querySelector(".container");
                cont.appendChild(clone);
            }
        }
    })

    Object.keys(downloads_array).forEach(function (key) {
        bar = document.getElementById(`val1_bar_${downloads_array[key].num}`);
        if (bar.value == '0') {

            d = document.getElementById(`window_${downloads_array[key].num}`);
            d.remove();
            delete downloads_array[key];
            console.log('remove', key);
        }
    })

}

async function get_del_info() {
    let response = await fetch('http://127.0.0.1:5000/get_download_deleted_info', {
        method: 'POST'
    });
    let json = await response.json();
    Object.keys(json).forEach(function(key) {
        if (!Object.keys(added_array).includes(key)) {
            added_array[key] = {'num': Object.keys(added_array).length + 1}
            row = document.querySelector('#row2');
            clone = row.content.cloneNode(true);

            d = clone.querySelector('div');
            d.id = `window2_${added_array[key].num}`

            sp = clone.querySelectorAll('span')[0];
            sp.id = `val2_text_${added_array[key].num}`;
            sp.textContent = json[key];

            cont = document.querySelector(".container2");
            cont.appendChild(clone);
        }
    })
}

downloads_array = {};
added_array = {};
setInterval(get_info, 1000);
setInterval(get_del_info, 1000);