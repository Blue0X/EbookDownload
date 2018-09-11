<?php
/**
* 电子书下载程序
*
* 电子书制作：
* 1. 配置好config.php
* 2. 运行生成html文件 （php main.php)
* 3. 用电子书制作软件生成电子书
*/

include('extract.php');
include('config.php');

$output = iconv('UTF-8', 'GB2312', 'output/' . $CONFIG['ebook_name']);
$dirFilename = 'output/tmp.dir';

if (!file_exists($output)) {
    create_fold();
}

extract_dir_urls();
extract_pages();

function extract_dir_urls() {
    global $CONFIG, $dirFilename;
    echo "Beginning...\n";
    $html = download_html($CONFIG['ebook_url']);
    $html = extract_part($html, $CONFIG['ebook_dir_tag_start'], $CONFIG['ebook_dir_tag_end']);
    $html = str_replace('</a>', '</A>', $html);
    $as = explode("</A>", $html);
    $urls = array();
    foreach ($as as $a) {
        $a = preg_replace('/^.*<a /i', '<a ', $a);
        $href = extract_url($a);
        if (!$href) continue;
        // print_r($a);exit;
        $text = strip_tags(html_entity_decode($a)); //标题
        $key = md5($href[0]);
        if ($CONFIG['ebook_page_url'] && !preg_match($CONFIG['ebook_page_url'], $href[0])) continue;
        if ($text && !isset($urls[$key])) {
            $urls[$key] = array(
                'url' => $href[0],
                'txt' => $text
            );
        }
    }
    file_put_contents($dirFilename, json_encode($urls));
    saveDir($urls);
    echo "Dir OK.\n";
}

function canonicalUrl($baseUrl, $url) {
    $urlParts = parse_url($baseUrl);
    $domain = $urlParts['scheme']  . '://'. $urlParts['host'];

    if ($url[0] == '/') {
        return $domain . $url;
    }
    elseif (preg_match('/^http:\/\//i', $url)) {
        return $url;
    }
    else {
        return dirname($baseUrl) . '/' . $url;
    }
}

function extract_pages() {
    global $CONFIG, $dirFilename;
    if (!file_exists($dirFilename)) {
        echo 'No dir file found!\n';
        return;
    }
    $txt = file_get_contents($dirFilename);
    $urls = json_decode($txt, true);
    $idx = 0;
    foreach ($urls as $url) {
        $idx++;
        echo "Download page {$url['url']}...\n";
        $pageUrl = canonicalUrl($CONFIG['ebook_url'], $url['url']);
        $html = download_html($pageUrl);
        $html = extract_part($html, $CONFIG['ebook_page_tag_start'], $CONFIG['ebook_page_tag_end']);

        $imageUrls = extract_image($html);
        if ($imageUrls) {
            $imageUrls = downloadImages($pageUrl, $imageUrls);
            $html = str_replace($imageUrls[0], $imageUrls[1], $html);
        }
        savePage($url['txt'], $html, $idx);
        echo "OK.\n";
        //if ($imageUrls) break;
    }
    echo "\nJob Done!";
}

function downloadImages($pageUrl, $imageUrls) {
    global $output;
    $replaceImages = array(array(), array());
    echo "Download images...\n";

    foreach ($imageUrls as $imageUrl) {
        $imageName = basename($imageUrl);
        $savePath = $output . "/image/" . $imageName;

        $replaceImages[0][] = $imageUrl;
        $replaceImages[1][] = 'image/' . $imageName;

        if (file_exists($savePath)) continue;

        $imageData = file_get_contents(canonicalUrl($pageUrl, $imageUrl));
        file_put_contents($savePath, $imageData);
    }

    return $replaceImages;
}

function savePage($title, &$data, $idx) {
    global $output;
    $html =<<<HTML
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>{$title}</title>
    <link href="css/style.css" rel="stylesheet" type="text/css">
  </head>
  <body class="ebook-page">
    <h3 class="ebook-title">{$title}</h3>
    <div class="ebook-content">
    {$data}
    </div>
  </body>
</html>
HTML;
    $idx = sprintf("%03d", $idx);
    file_put_contents($output . "/page{$idx}.html", $html);
}

function saveDir($urls) {
    global $output;

    $dirs = '';
    $idx = 0;
    foreach ($urls as $url) {
        $idx++;
        $href = 'page' . sprintf("%03d", $idx) . '.html';
        $dirs .= "<p><a href=\"{$href}\">{$url['txt']}</a></p>\n";
    }
    $html =<<<HTML
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>目录</title>
    <link href="css/style.css" rel="stylesheet" type="text/css">
  </head>
  <body class="ebook-index">
    <h3>目录</h3>
    {$dirs}
  </body>
</html>
HTML;
    file_put_contents($output . "/index.html", $html);
}

function create_fold() {
    global $output;
    mkdir($output, 0777, true);
    mkdir($output . '/image');
    mkdir($output . '/css');
    file_put_contents($output . '/css/style.css', ".ebook-index{}\n.ebook-page{}");
}