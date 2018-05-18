$.fn.atwho.debug = true;

var query_cache = '';
var cachequeryMentions = [], itemsMentions;
var CUSTOM_CALLBACKS = {
    filter: function (query, data, searchKey) {
        //console.log(arguments);
        return data;
    },
    sorter: function (query, items, searchKey) {
        //console.log(arguments);
        var i, len;
        if (!query) {
            return items;
        }
        return items.sort(function (a, b) {
            for (i= 0, len = searchKey.length; i < len; i++){
                key = searchKey[i];
                va = a[key].toLowerCase().indexOf(query.toLowerCase());
                vb = b[key].toLowerCase().indexOf(query.toLowerCase());
                if (i == (len - 1)){
                    return va - vb
                }else{
                    if(va != vb){
                        return va - vb
                    }
                }
           }
        })
    },
    remoteFilter: function (query, render_view) {
        var thisVal = query,
            self= $(this);
        if (!self.data('active') && thisVal.length >= 1){
            self.data('active', true);
            itemsMentions = cachequeryMentions[thisVal];
            if (typeof itemsMentions == "object") {
                render_view(itemsMentions);
            }else{
                if (self.xhr) {
                    self.xhr.abort();
                }
                self.xhr = $.getJSON("/api2/search-user/", {
                    q: thisVal
                }, function (data) {
                    console.log(data);
                    var info = data['users'];
                    cachequeryMentions[thisVal] = info;
                    render_view(info);
                });
            }
            self.data('active', false);
        }
    }
};

var CONFIG = {
    at: '@',
    alias: 'at',  // for event name suffix
    data: [],
    searchKey: ['name', 'email'],  // used in callbacks filter and sorted
    displayTpl: '<li><img src="${avatar_url}" width="36" height="36" class="avatar"><span>${name}</br><small>(${email})</small></span></li>',
    insertTpl: '${atwho-at}{${email}}',
    suffix: ' ',
    startWithSpace: true,
    limit: 7,
    maxLen: 20,
    callbacks: CUSTOM_CALLBACKS
};
function search_users(name){
    var that = this;
    $.ajax({
        url: '/api2/search-user/',
        data: {q: name}
    })
        .done(function (msg) {
            var data = msg.users;
            $(that).atwho('load', '@', data).atwho('run');
        });
}

//var $inputor = $('#inputor');
//$inputor.atwho(CONFIG);
//$inputor.on("matched-at.atwho", function(event, flag, query) {
//    if (query != query_cache && query){
//        search_users.call(this, query);
//        query_cache = query;
//    }else{
//        //console.log("matched.atwho matched " + flag + ' ' + query);
//    }
//});

var $editor = $('#editor');
$editor.atwho(CONFIG);
//$editor.on("matched-at.atwho", function(event, flag, query) {
//    //console.log(arguments);
//    if (query != query_cache && query){
//        $.ajax({
//            url: '/api2/search-user/',
//            data: {q: query}
//        })
//            .done(function (msg) {
//                var data = msg.users;
//                console.log(arguments, data);
//                $editor.atwho('load', flag, data).atwho('run');
//            });
//        query_cache = query;
//    }
//});

var editor = document.querySelector('#editor');
editor.addEventListener('input',function(e){
    var sel = window.getSelection();
    var focusNode = sel.focusNode;
    var sele = focusNode.parentElement;
    console.log(sele.nodeName);
    if(sele.nodeName == 'CODE'){
        var range = document.createRange();
        range.selectNode(focusNode);
        sel.removeAllRanges();
        sel.addRange(range);
        document.execCommand('delete');
        document.execCommand('insertHTML', true,' ');
    }
    //console.log(sel.baseNode == sel.focusNode == sel.extentNode);
    //console.log(e);
});

$('.oneselect').click(function (e) {
    console.log(e, this);
    var sel = window.getSelection();
    var range = document.createRange();
    range.selectNode(this);
    sel.removeAllRanges();
    sel.addRange(range);
});