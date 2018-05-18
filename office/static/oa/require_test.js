//requirejs.config({
//    baseUrl: 'lib',
//    paths: {
//        app: '../app'
//    }
//});
requirejs(["helper/util"], function(util) {
    //This function is called when scripts/helper/util.js is loaded.
    //If util.js calls define(), then this function is not fired until
    //util's dependencies have loaded, and the util argument will hold
    //the module value for "helper/util".
    var t = document.querySelector('h1');
    var a = document.querySelectorAll('script').length;
    var b = document.querySelectorAll('p').length;
    var n = util.add(a,b);
    setTimeout(function(){t.innerText=n},1000)
});