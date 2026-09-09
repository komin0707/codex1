package com.komin.unlocknoti;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Typeface;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class MainActivity extends Activity {
    private ListView listView;
    private TextView emptyView;
    private NotificationDb db;
    private List<NotificationDb.Item> items;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        db = new NotificationDb(this);
        setContentView(buildUi());
    }

    @Override
    protected void onResume() {
        super.onResume();
        reload();
    }

    private View buildUi() {
        int pad = dp(16);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(pad, dp(12), pad, 0);

        TextView title = new TextView(this);
        title.setText("알림 전체보기");
        title.setTextSize(28);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        title.setPadding(0, dp(8), 0, dp(4));
        root.addView(title, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView subtitle = new TextView(this);
        subtitle.setText("잠금 해제 직후 자동으로 열리고, 새 알림을 계속 보관합니다.");
        subtitle.setTextSize(14);
        subtitle.setAlpha(0.7f);
        subtitle.setPadding(0, 0, 0, dp(10));
        root.addView(subtitle);

        LinearLayout actions = new LinearLayout(this);
        actions.setOrientation(LinearLayout.HORIZONTAL);

        Button notificationAccess = new Button(this);
        notificationAccess.setText("1. 알림 접근");
        notificationAccess.setOnClickListener(v -> {
            try {
                startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS));
            } catch (Exception e) {
                startActivity(new Intent("android.settings.ACTION_NOTIFICATION_LISTENER_SETTINGS"));
            }
        });
        actions.addView(notificationAccess, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        Button autoOpen = new Button(this);
        autoOpen.setText("2. 자동 열기");
        autoOpen.setOnClickListener(v -> startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)));
        actions.addView(autoOpen, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        root.addView(actions);

        LinearLayout tools = new LinearLayout(this);
        tools.setOrientation(LinearLayout.HORIZONTAL);

        Button refresh = new Button(this);
        refresh.setText("새로고침");
        refresh.setOnClickListener(v -> reload());
        tools.addView(refresh, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        Button clear = new Button(this);
        clear.setText("기록 삭제");
        clear.setOnClickListener(v -> {
            db.clearAll();
            reload();
        });
        tools.addView(clear, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        root.addView(tools);

        emptyView = new TextView(this);
        emptyView.setText("저장된 알림이 없습니다.\n위의 ‘알림 접근’을 한 번 켜면 이후 알림부터 기록됩니다.");
        emptyView.setGravity(Gravity.CENTER);
        emptyView.setTextSize(16);
        emptyView.setPadding(pad, dp(50), pad, dp(50));

        listView = new ListView(this);
        listView.setDividerHeight(0);
        listView.setClipToPadding(false);
        listView.setPadding(0, dp(6), 0, dp(20));

        root.addView(emptyView, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        root.addView(listView, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        return root;
    }

    private void reload() {
        items = db.recent(1000);
        boolean empty = items == null || items.isEmpty();
        emptyView.setVisibility(empty ? View.VISIBLE : View.GONE);
        listView.setVisibility(empty ? View.GONE : View.VISIBLE);
        if (!empty) listView.setAdapter(new NotiAdapter());
    }

    private class NotiAdapter extends BaseAdapter {
        private final SimpleDateFormat formatter = new SimpleDateFormat("M/d HH:mm", Locale.KOREA);

        @Override public int getCount() { return items.size(); }
        @Override public Object getItem(int position) { return items.get(position); }
        @Override public long getItemId(int position) { return position; }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            NotificationDb.Item item = items.get(position);
            LinearLayout card = new LinearLayout(MainActivity.this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setPadding(dp(14), dp(10), dp(14), dp(10));

            TextView app = new TextView(MainActivity.this);
            app.setText(item.appName + "   " + formatter.format(new Date(item.postedAt)));
            app.setTextSize(12);
            app.setAlpha(0.6f);
            card.addView(app);

            if (item.title != null && !item.title.isEmpty()) {
                TextView t = new TextView(MainActivity.this);
                t.setText(item.title);
                t.setTextSize(16);
                t.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
                t.setPadding(0, dp(2), 0, 0);
                card.addView(t);
            }

            if (item.body != null && !item.body.isEmpty()) {
                TextView b = new TextView(MainActivity.this);
                b.setText(item.body);
                b.setTextSize(15);
                b.setPadding(0, dp(2), 0, dp(4));
                b.setMaxLines(8);
                card.addView(b);
            }

            View line = new View(MainActivity.this);
            line.setBackgroundColor(0x22000000);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(1));
            lp.setMargins(0, dp(5), 0, 0);
            card.addView(line, lp);
            return card;
        }
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
