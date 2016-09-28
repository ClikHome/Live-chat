function setCookie(key, value, path, expires) {
    expires = expires || 60 * 60 * 24 * 7;
    path = path || '/';

    if (typeof expires == "number" && expires) {
        expires = new Date(new Date().getTime() + expires * 1000);
    }

    if (expires && expires.toUTCString) {
        expires = expires.toUTCString();
    }

    value = encodeURIComponent(value);
    var new_cookie = key + "=" + value + '; ';
    new_cookie += 'path=' + path + '; ';
    new_cookie += 'expires=' + expires;

  document.cookie = new_cookie;
}