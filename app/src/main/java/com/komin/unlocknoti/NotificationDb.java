package com.komin.unlocknoti;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

import java.util.ArrayList;
import java.util.List;

public class NotificationDb extends SQLiteOpenHelper {
    private static final String DB_NAME = "notifications.db";
    private static final int DB_VERSION = 1;

    public NotificationDb(Context context) {
        super(context, DB_NAME, null, DB_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE notifications (" +
                "id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "pkg TEXT NOT NULL," +
                "app_name TEXT," +
                "title TEXT," +
                "body TEXT," +
                "posted_at INTEGER NOT NULL," +
                "fingerprint TEXT UNIQUE NOT NULL)");
        db.execSQL("CREATE INDEX idx_posted_at ON notifications(posted_at DESC)");
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) { }

    public void insert(String pkg, String appName, String title, String body, long postedAt, String fingerprint) {
        ContentValues values = new ContentValues();
        values.put("pkg", pkg);
        values.put("app_name", appName);
        values.put("title", title);
        values.put("body", body);
        values.put("posted_at", postedAt);
        values.put("fingerprint", fingerprint);
        getWritableDatabase().insertWithOnConflict("notifications", null, values, SQLiteDatabase.CONFLICT_IGNORE);
    }

    public List<Item> recent(int limit) {
        ArrayList<Item> out = new ArrayList<>();
        Cursor c = getReadableDatabase().query(
                "notifications",
                new String[]{"app_name", "title", "body", "posted_at"},
                null, null, null, null,
                "posted_at DESC",
                String.valueOf(limit)
        );
        try {
            while (c.moveToNext()) {
                out.add(new Item(c.getString(0), c.getString(1), c.getString(2), c.getLong(3)));
            }
        } finally {
            c.close();
        }
        return out;
    }

    public void clearAll() {
        getWritableDatabase().delete("notifications", null, null);
    }

    public static class Item {
        public final String appName;
        public final String title;
        public final String body;
        public final long postedAt;

        public Item(String appName, String title, String body, long postedAt) {
            this.appName = appName;
            this.title = title;
            this.body = body;
            this.postedAt = postedAt;
        }
    }
}
