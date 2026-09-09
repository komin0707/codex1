package com.komin.unlocknoti;

import android.accessibilityservice.AccessibilityService;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Build;
import android.os.SystemClock;
import android.view.accessibility.AccessibilityEvent;

public class UnlockAccessibilityService extends AccessibilityService {
    private long lastLaunchAt = 0L;
    private BroadcastReceiver receiver;

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        receiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                if (Intent.ACTION_USER_PRESENT.equals(intent.getAction())) {
                    launchList();
                }
            }
        };
        IntentFilter filter = new IntentFilter(Intent.ACTION_USER_PRESENT);
        if (Build.VERSION.SDK_INT >= 33) {
            registerReceiver(receiver, filter, Context.RECEIVER_NOT_EXPORTED);
        } else {
            registerReceiver(receiver, filter);
        }
    }

    private void launchList() {
        long now = SystemClock.elapsedRealtime();
        if (now - lastLaunchAt < 1500) return;
        lastLaunchAt = now;

        Intent i = new Intent(this, MainActivity.class);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        startActivity(i);
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) { }

    @Override
    public void onInterrupt() { }

    @Override
    public void onDestroy() {
        if (receiver != null) {
            try { unregisterReceiver(receiver); } catch (Exception ignored) { }
        }
        super.onDestroy();
    }
}
