<?php

/**
 * 下载html网页，必要时转码
 */
function download_html($url, $page_charset = 'utf-8') {
    if (function_exists('curl_init')) {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 5.1; rv:14.0) Gecko/20100101 Firefox/14.0.1');
        $urlinfo = parse_url($url);
        $headers = array(
            'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Cache-Control: max-age=0',
            'Connection: keep-alive',
            'Accept-Language: en-us,en;q=0.5',
            'Host: ' . $urlinfo['host'],
        );
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($ch, CURLOPT_REFERER, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, TRUE);
        curl_setopt($ch, CURLOPT_URL, $url);
        $html = curl_exec($ch);
        curl_close($ch);
    }
    else  {
        $ctx = stream_context_create(
            array(
                'http' => array('timeout' => 30) //设置一个超时时间，单位为秒
            )
        );
        $html = file_get_contents($url, 0, $ctx);
    }

    if(!$html) return false;

    if ('utf-8' != $page_charset && 'iso-8859-1' != $page_charset) {
        $html = iconv($page_charset, 'utf-8//IGNORE', $html);
    }

    return $html;
}

/**
 * 截取部分HTML内容
 */
function extract_part($html, $start, $end) {
    if (empty($html)) return false;

    $html = str_replace(array("\r", "\n"), "", $html);
    $start = str_replace(array("\r", "\n"), "", $start);
    $end = str_replace(array("\r", "\n"), "", $end);

    $html = explode(trim($start), $html, 2);
    if(is_array($html) && count($html) == 1) return false;//没有匹配

    $html = explode(trim($end), $html[1], 2);
    if(count($html) == 1) return false;

    return trim($html[0]);
}

/**
 * 从html中提取链接地址
 */
function extract_url($html) {
    if (preg_match_all('/<a[^>]*href=[\'"]?([^>\'"\s]*)[\'"]?[^>]*>/i', $html, $out)) {
        return $out[1];
    }
    return array();
}

/**
 * 从html中提取图片地址
 */
function extract_image($html) {
    if (preg_match_all('/<img[^>]*src=[\'"]?([^>\'"\s]*)[\'"]?[^>]*>/i', $html, $out)) {
        return $out[1];
    }
    return array();
}