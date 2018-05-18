/*
@at who
 */
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
            var va, vb, key;
            for (i = 0, len = searchKey.length; i < len; i++) {
                key = searchKey[i];
                va = a[key].toLowerCase().indexOf(query.toLowerCase());
                vb = b[key].toLowerCase().indexOf(query.toLowerCase());
                if (i == (len - 1)) {
                    return va - vb
                } else {
                    if (va != vb) {
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
                    //console.log(data);
                    var info = data['users'];
                    cachequeryMentions[thisVal] = info;
                    render_view(info);
                });
            }
            self.data('active', false);
        }
    }
};
var displayTpl = '<li><img src="${avatar_url}" width="32" height="32" class="avatar"><span>${name}</br><small>(${email})</small></span></li>';
var insertTpl = '{${name}}(${email})';  // used in views.find_at
var headerTpl = '<p class="atwho-header">请输入：</p>';
var CONFIG = {
    at: '@',
    alias: 'at',  // for event name suffix
    data: [],
    searchKey: ['name', 'email'],  // used in callbacks filter and sorted
    displayTpl: displayTpl,
    insertTpl: insertTpl,
    //headerTpl: headerTpl,
    startWithSpace: true,
    limit: 10,
    maxLen: 20,
    callbacks: CUSTOM_CALLBACKS
};
$('.at-inputor').atwho(CONFIG);
//function search_users(name){
//    $.ajax({
//        url: '/api2/search-user/',
//        data: {q: name}
//    })
//        .done(function (msg) {
//            var data = msg.users;
//            console.log('ajax', data);
//            $inputor.atwho('load', '@', data).atwho('run');
//        });
//}
//$inputor.on("matched-at.atwho", function(event, flag, query) {
//    if (query != query_cache && query){
//        search_users(query);
//        query_cache = query;
//    }else{
//        console.log("matched.atwho matched " + flag + ' ' + query);
//    }
//});
/*
contenteditable post
 */
var copyContent = function (that) {
    console.log(that);
    var contenteditable = that.parentNode.querySelector('[contenteditable]');
    var textarea = that.querySelector('textarea');
    if (textarea.value == '') {
        textarea.value = contenteditable.innerText;
    }
    return true;
};
/*
editor widget
 */
var get_edit_url = function (id) {
  return '/oa/commit/'+id+'/edit'
};
var editor_control = document.querySelector('#editor-control');
// open editor widget and write the commit content
$(".btn2edit").on('click', function (e) {
    var editid = $(this).data('id');
    //console.log(editid);
    $.getJSON(get_edit_url(editid))
        .done(function (data) {
            editor_control.querySelector('form').action = data.url;
            //todo: render commit @content
            editor_control.querySelector('textarea').value = data.commit;
            $(editor_control).addClass('open');
            movePanels('300px');
        })
});
// close editor widget
$(editor_control).find(".toggler").on('click', function(){
    $(editor_control).removeClass('open');
    $(editor_control).removeAttr('style');
    $('#content').removeAttr('style');
});
/*
editor widget resize
*/
var div, lastMousePos, originalPos, originalDivHeight, wrappedPerformDrag, wrappedEndDrag;
var min = 230;
var startDrag = function (e, opts) {
    div = $(e.data.el);
    div.addClass('clear-transitions');
    div.blur();
    lastMousePos = mousePosition(e).y;
    originalPos = lastMousePos;
    originalDivHeight = div.height();
    wrappedPerformDrag = (function() {
        return function(e) {
            return performDrag(e, opts);
        };
    })();
    wrappedEndDrag = (function() {
        return function(e) {
            return endDrag(e, opts);
        };
    })();
    $(document).mousemove(wrappedPerformDrag).mouseup(wrappedEndDrag);
    return false;

};
var performDrag = function (e, opts) {
    var size, sizePx, thisMousePos;
    thisMousePos = mousePosition(e).y;
    size = originalDivHeight + (originalPos - thisMousePos);
    lastMousePos = thisMousePos;

    var maxHeight = $(window).height();
    if (opts.maxHeight) {
        maxHeight = opts.maxHeight(maxHeight);
    }
    size = Math.min(size, maxHeight);
    size = Math.max(min, size);
    sizePx = size + "px";
    //console.log(size);
    if (typeof opts.onDrag === "function") {
        opts.onDrag(sizePx);
    }
    //console.log(sizePx);
    div.height(sizePx);
    if (size < min) {
        endDrag(e, opts);
    }
    return false;
};
var endDrag = function (e, opts) {
    $(document).unbind("mousemove", wrappedPerformDrag).unbind("mouseup", wrappedEndDrag);
    div.removeClass('clear-transitions');
    div.focus();
    if (typeof opts.resize === "function") {
        opts.resize();
    }
    div = null;
    //console.log('endDrag')
};
var mousePosition = function(e) {
  return {
    x: e.clientX + document.documentElement.scrollLeft,
    y: e.clientY + document.documentElement.scrollTop
  };
};
var movePanels = function (sizePx) {
    $('#content').css('padding-bottom', sizePx);
};
$.fn.DivResizer = function (opts) {
    return this.each(function () {
        var start, grippie;
        div = $(this);
        start = function () {
            return function (e) {
             return startDrag(e, opts);
            }
        };
        grippie = div.find('.grippie').bind("mousedown",{
            el: this
        }, start());
    });
};
// usage
$(editor_control).DivResizer({
    onDrag: function (sizePx) {
        //console.log('onDrag', sizePx);
        return movePanels(sizePx);
    },
    maxHeight: function (winHeight) {
        //console.log('maxHeight', winHeight);
        return winHeight - $('.my-navbar').height();
    },
    //maxHeight: false,
    resize: function () {
        return false;
    }
});
