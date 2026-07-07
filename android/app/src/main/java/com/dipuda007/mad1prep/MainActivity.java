package com.dipuda007.mad1prep;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

/**
 * MAD-1 Prep for Android: a WebView showing the bundled prep-app pages
 * (copied into assets/www/ by the GitHub Actions build). Fully offline.
 */
public class MainActivity extends Activity {

    private WebView web;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);   // theme toggle + progress tracking
        s.setDomStorageEnabled(true);   // localStorage for saved progress
        s.setAllowFileAccess(true);     // pages live on file:///android_asset
        web.setWebViewClient(new WebViewClient());
        web.loadUrl("file:///android_asset/www/index.html");
        setContentView(web);
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) {
            web.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
