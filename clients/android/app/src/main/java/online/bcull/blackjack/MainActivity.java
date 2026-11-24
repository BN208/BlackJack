package online.bcull.blackjack;

import android.app.Activity;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.text.InputType;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    private static final String DEFAULT_SERVER = "https://blackjack.bcull.online";
    private static final String PREFERENCES = "blackjack-client";
    private static final String SERVER_KEY = "server-url";

    private LinearLayout serverForm;
    private Button changeServerButton;
    private EditText serverAddressInput;
    private WebView webView;
    private SharedPreferences preferences;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        preferences = getSharedPreferences(PREFERENCES, MODE_PRIVATE);
        getWindow().setStatusBarColor(Color.rgb(17, 99, 5));
        getWindow().setNavigationBarColor(Color.rgb(17, 99, 5));
        buildInterface();
        showServerForm();
    }

    private void buildInterface() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(25, 142, 7));

        changeServerButton = new Button(this);
        changeServerButton.setText("Change Server");
        changeServerButton.setOnClickListener(view -> showServerForm());
        root.addView(changeServerButton, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, wrapContent()
        ));

        serverForm = new LinearLayout(this);
        serverForm.setOrientation(LinearLayout.VERTICAL);
        serverForm.setPadding(dp(24), dp(28), dp(24), dp(24));

        TextView title = new TextView(this);
        title.setText("BlackJack");
        title.setTextColor(Color.WHITE);
        title.setTextSize(26);
        title.setPadding(0, 0, 0, dp(8));
        serverForm.addView(title, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, wrapContent()
        ));

        TextView instructions = new TextView(this);
        instructions.setText("Enter the address of the BlackJack server you want to join.");
        instructions.setTextColor(Color.WHITE);
        instructions.setTextSize(16);
        serverForm.addView(instructions, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, wrapContent()
        ));

        serverAddressInput = new EditText(this);
        serverAddressInput.setSingleLine(true);
        serverAddressInput.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        serverAddressInput.setHint(DEFAULT_SERVER);
        serverAddressInput.setText(preferences.getString(SERVER_KEY, DEFAULT_SERVER));
        serverAddressInput.setSelectAllOnFocus(true);
        LinearLayout.LayoutParams inputLayout = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, wrapContent()
        );
        inputLayout.topMargin = dp(20);
        serverForm.addView(serverAddressInput, inputLayout);

        Button openButton = new Button(this);
        openButton.setText("Connect");
        openButton.setOnClickListener(view -> openServer());
        LinearLayout.LayoutParams buttonLayout = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, wrapContent()
        );
        buttonLayout.topMargin = dp(12);
        serverForm.addView(openButton, buttonLayout);
        root.addView(serverForm, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, wrapContent()
        ));

        webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true);
        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return !isHttpUrl(request.getUrl());
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return !isHttpUrl(Uri.parse(url));
            }
        });
        root.addView(webView, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, 0, 1
        ));
        setContentView(root);
    }

    private void openServer() {
        String address = normalizeServerAddress(serverAddressInput.getText().toString());
        if (address == null) {
            serverAddressInput.setError("Enter a valid HTTP or HTTPS server address");
            return;
        }
        preferences.edit().putString(SERVER_KEY, address).apply();
        webView.loadUrl(address);
        serverForm.setVisibility(View.GONE);
        changeServerButton.setVisibility(View.VISIBLE);
        webView.setVisibility(View.VISIBLE);
    }

    private String normalizeServerAddress(String value) {
        String address = value.trim();
        if (address.isEmpty()) return null;
        if (!address.matches("(?i)^[a-z][a-z0-9+.-]*://.*")) {
            address = "https://" + address;
        }

        Uri uri = Uri.parse(address);
        String scheme = uri.getScheme();
        if (uri.getHost() == null || uri.getUserInfo() != null
            || !("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme))) {
            return null;
        }
        return uri.toString();
    }

    private boolean isHttpUrl(Uri uri) {
        String scheme = uri.getScheme();
        return "http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme);
    }

    private void showServerForm() {
        serverForm.setVisibility(View.VISIBLE);
        changeServerButton.setVisibility(View.GONE);
        webView.setVisibility(View.GONE);
    }

    @Override
    public void onBackPressed() {
        if (webView.getVisibility() == View.VISIBLE && webView.canGoBack()) {
            webView.goBack();
        } else if (webView.getVisibility() == View.VISIBLE) {
            showServerForm();
        } else {
            super.onBackPressed();
        }
    }

    private int wrapContent() {
        return LinearLayout.LayoutParams.WRAP_CONTENT;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
