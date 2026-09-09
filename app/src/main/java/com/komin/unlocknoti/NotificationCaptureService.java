package com.komin.unlocknoti;

import android.app.Notification;
import android.content.pm.ApplicationInfo;
import android.os.Bundle;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import android.text.TextUtils;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

public class NotificationCaptureService extends NotificationListenerService {
    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        if (sbn == null || sbn.getNotification() == null) return;
        if (getPackageName().equals(sbn.getPackageName())) return;

        Notification n = sbn.getNotification();
        Bundle e = n.extras;
        String title = toStringSafe(e.getCharSequence(Notification.EXTRA_TITLE));
        String body = toStringSafe(e.getCharSequence(Notification.EXTRA_BIG_TEXT));
        if (TextUtils.isEmpty(body)) body = toStringSafe(e.getCharSequence(Notification.EXTRA_TEXT));

        CharSequence[] lines = e.getCharSequenceArray(Notification.EXTRA_TEXT_LINES);
        if (lines != null && lines.length > 0) {
            StringBuilder b = new StringBuilder();
            for (CharSequence line : lines) {
                if (line == null) continue;
                if (b.length() > 0) b.append("\n");
                b.append(line);
            }
            if (b.length() > body.length()) body = b.toString();
        }

        if (TextUtils.isEmpty(title) && TextUtils.isEmpty(body)) return;

        String appName = sbn.getPackageName();
        try {
            ApplicationInfo info = getPackageManager().getApplicationInfo(sbn.getPackageName(), 0);
            appName = getPackageManager().getApplicationLabel(info).toString();
        } catch (Exception ignored) { }

        long when = sbn.getPostTime();
        String fp = sha256(sbn.getPackageName() + "|" + title + "|" + body + "|" + when);
        new NotificationDb(this).insert(sbn.getPackageName(), appName, title, body, when, fp);
    }

    private static String toStringSafe(CharSequence c) {
        return c == null ? "" : c.toString();
    }

    private static String sha256(String s) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] d = md.digest(s.getBytes(StandardCharsets.UTF_8));
            StringBuilder out = new StringBuilder();
            for (byte b : d) out.append(String.format("%02x", b));
            return out.toString();
        } catch (Exception e) {
            return String.valueOf(s.hashCode());
        }
    }
}
