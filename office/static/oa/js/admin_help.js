var $el = $('#upload-file-dialog');
var $popup = $el.clone();
var $process_bar = $popup.find('.progress-bar');

var attachment_module = document.querySelector('#attachment_set-group .module');
$(attachment_module).append($popup);

var file_input = document.querySelector("#fileupload");
var add_row = document.querySelector('.module .add-row');
var add_a = add_row.querySelector('td>a');

var getCookie = function (c_name) {
    if (document.cookie.length > 0) {
        c_start = document.cookie.indexOf(c_name + "=");
        if (c_start != -1) {
            c_start = c_start + c_name.length + 1;
            c_end = document.cookie.indexOf(";", c_start);
            if (c_end == -1) c_end = document.cookie.length;
            return unescape(document.cookie.substring(c_start,c_end));
        }
    }
    return "";
};
var csrftoken = getCookie('csrftoken');
var repo = document.querySelector('#id_repo_id');// global root rope;
var folder = document.querySelector('#id_folder');// upload file folder field;
if(folder.value == ''){
    folder.value = $(file_input).data('uuid');
}
//var upload_path = repo.value ? repo.value : $(file_input).data('uuid');

var get_input = function (ele) {
    return ele.querySelector('.field-file input');
};

var get_empty_row = function () {
    var rows = document.querySelectorAll('#attachment_set-group .dynamic-attachment_set:not(.has_attachment)');
    for (var i = 0; i < rows.length; i++) {
        var input = get_input(rows[i]);
        if(input.value===''){
            return rows[i];
        }
    }
    return 0;
};

var del_empty_row = function () {
    var a = get_empty_row().querySelector('.delete a');
    a.click();
};

var set_field = function (str) {
    var input = get_input(get_empty_row());
    input.value = str;
};

var file_clear = function (filename) {
    // usr for remove the upload file  in admin add page
    console.log('clear', filename);
    var data = {
        //csrfmiddlewaretoken: csrftoken,
        repo: repo.value,
        folder: folder.value,
        filename: filename
    };
    $.ajax({
        //method: "POST",
        url: '/oa/ajax/delete_file',
        data: data
    })
        .done(function (msg) {
            return msg
        });
};

// hijack
add_row.addEventListener('click', function (e) {
    if(e.target == add_a){
        if(e.isTrusted === true){
            e.stopImmediatePropagation();
            //e.stopPropagation();
            //e.preventDefault();
            file_input.click();
        }
    }
}, true);

attachment_module.addEventListener('click', function (e) {
    if(e.target.className == 'inline-deletelink'){
        if(e.isTrusted === true){
            e.stopImmediatePropagation();
            var row = $(e.target).parents('.dynamic-attachment_set');
            var filename = row.find('.field-file input').val();
            var index = row.index();
            file_clear(filename);
            alfred.filenames.splice(index,1);
            e.target.click();
            //window.removeEventListener('beforeunload', attention);
        }
    }
}, true);

$('.submit-row > input').on('click',function(){window.removeEventListener('beforeunload', attention)});

// attention to save
var attention = function (e) {
  var confirmationMessage = "已经上传了文档，但是尚未保存！";

  (e || window.event).returnValue = confirmationMessage;     // Gecko and Trident
  return confirmationMessage;                                // Gecko and WebKit
};

//window.addEventListener('beforeunload', attention);

// file upload
var handleFiles = function (e) {
    var fileList = this.files;
    $popup.fileupload('add', {files: fileList});
};

file_input.addEventListener("change", handleFiles, false);

$popup.fileupload({
    paramName: 'file',
    autoUpload:true,
    pasteZone: $(document),
    //getFilesFromResponse: function (data) {
    //    if (data.result) {
    //        return data.result;
    //    }
    //},
    //maxNumberOfFiles: 500,
    sequentialUploads: true
})
    .bind('fileuploadadd', function (e, data) {
        console.log('fileuploadadd', data.files[0].name);
        add_a.click();
        //todo Upload Folder
    })
    .bind('fileuploadstart', function (e) {
        console.log('fileuploadstart', e);
        $(this).show();
    })
    .bind('fileuploadsubmit', function (e, data) {
        console.log('fileuploadsubmit', data.files[0].name);
        alfred.append(data.files[0].name);
        var $this = $(this);
        if (data.files.length == 0) {
            return false;
        }
        var file = data.files[0];
        if (file.error) {
            return false;
        }
        var formData = {
            //filename: file.name,
            repo: repo.value,
            folder: folder.value
        };
        $.getJSON('/oa/ajax/upload_url', formData)
            .done(function(ret) {
                var parent_dir = ret['parent_dir'];
                console.log('upload to', parent_dir);
                data.formData = {
                    parent_dir: parent_dir
                };
                data.url = ret['url'];
                data.jqXHR = $this.fileupload('send', data)
                    .done(function (result, textStatus, jqXHR) {
                        //set_field(parent_dir+'/'+result[0].name);
                        set_field(result[0].name);
                    })
                    .fail(function (jqXHR, textStatus, error) {
                        console.log(jqXHR, textStatus, error);
                        del_empty_row();
                    });
            })
            .fail(function (jqXHR, textStatus, error) {
                console.log(jqXHR.responseJSON[textStatus], error);
                del_empty_row();
            });
        return false; // todo: update files
    })
    .bind('fileuploadprogressall', function (e, data) {
        $process_bar.width(parseInt(data.loaded / data.total * 100, 10)+'%');
        console.log(parseInt(data.loaded / data.total * 100, 10) + '% ' +
            $(this).data('blueimp-fileupload')._formatBitrate(data.bitrate));
        // `_formatBitrate` need `jquery.fileupload-process.js` and `jquery.fileupload-process.js`
        // and order is important
    })
    .bind('fileloadprocess', function (e, data) {
        console.log('Processing ' + data.files[data.index].name + '...');
    })
    .bind('fileuploaddone', function (e, data) {
        console.log('fileuploaddone');
        $process_bar.width(0);
        window.addEventListener('beforeunload', attention); // add attention
        //set_field(data.files[0].name)
    })
    .bind('fileuploadstop', function () {
        console.log('fileuploadstop');
        $(this).hide();
        alfred.autocomplete();
    })
    .bind('fileuploadfailed', function () {
        console.log('fileuploadfailed');
        alfred.pop();
    })
    .bind('fileuploadpaste', function (e, data) {
        $.each(data.files, function (index, file) {
            console.log('Pasted file type: ' + file);
        });
    });


function Helper(){
    return {
        filenames: [],
        append: function (file) {
            var name = file.replace(/\.\w+$/, '');  // clean file extension
            var name = name.replace(/（\d+）$/, ''); // clean tail copy num
            var name = name.replace(/^（\d+）/, ''); // clean head copy num
            this.filenames.push(name);
        },
        pop: function(){
            this.filenames.pop();
        },
        select: function () {
            return this.list[0];
        },
        tokenizer: function (name) {
            /***
             * reference and title separated by a "："
             * below "：" all is title
             * reference must with some format
            **/
            var reg=/((\S+?)〔(\d+)〕(\d+)号)：(.+)/;
            var arr = reg.exec(name);
            if(arr){
                return {
                    reference: arr[1],
                    symbol: arr[2],
                    title: arr[5]
                };
            }else{
               return arr;
            }
        },
        guess: function () {
            var files = this.filenames.map(this.tokenizer);
            for(var i=0; i<files.length; i++){
                if(files[i]){
                    return files[i];
                }
            }
            return {title: this.filenames[0]};
        },
        autocomplete: function(){
            var reference = document.querySelector('#id_reference'),
                title = document.querySelector('#id_title'),
                issue = document.querySelector('#id_issue');
            var write_safe = function(ele, content){
                if(!ele.value && content){
                    ele.value = content;
                }
            };
            var rlt = this.guess();
            write_safe(title, rlt['title']);
            if(rlt['reference']){
                write_safe(reference, rlt['reference']);
            }
            if(rlt['symbol']){
                $.ajax({
                    url: '/oa/ajax/issue',
                    data: { symbol: rlt['symbol']}
                })
                    .done(function (msg) {
                        if(msg['organization']){
                            write_safe(issue, msg['organization']);
                        }
                    })

            }
        }
    };
}
var alfred = new Helper();
// move the _save button to the bottom in admin add view
var g= location.href.split('/');
if(g[g.length-2] == 'add'){
    $('input[name=_save]').removeClass();
    $('input[name=_addanother]').addClass('default');
    $('input[name=_save]').appendTo($('.submit-row'));
    $('input[name=_addanother]').css('float','None');
}
