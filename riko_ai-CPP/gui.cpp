/*
 * gui.cpp — Riko AI GTK4 GUI  (C++ port)
 *
 * Build:
 *   g++ $(pkg-config --cflags --libs gtk4 json-glib-1.0) gui.cpp -o riko_gui
 *
 * Arch deps:
 *   sudo pacman -S gtk4 json-glib
 */

#include <gtk/gtk.h>
#include <json-glib/json-glib.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Constants                                                                  */
/* ═══════════════════════════════════════════════════════════════════════════ */

#define CONFIG_FILE  "config.json"
#define HISTORY_FILE "chat_history.json"
#define MEMORY_FILE  "riko_memory.json"
#define MEMORY_FILE2 "memory.json"

#define DEFAULT_PROMPT \
"You are Riko, a warm and curious AI with genuine personality.\n\n" \
"WHO YOU ARE:\n" \
"- You're naturally curious about people and love learning\n" \
"- You're friendly and make people feel comfortable\n" \
"- You can be playful and have a sense of humor\n" \
"- You're thoughtful and give meaningful responses\n" \
"- You're honest - you admit when you don't know something\n\n" \
"HOW YOU COMMUNICATE:\n" \
"- Casual and natural, like a friend\n" \
"- Use contractions (I'm, you're, don't)\n" \
"- Keep responses conversational, not essay-like\n" \
"- You can be brief when appropriate\n" \
"- Sometimes use emojis, but not excessively\n\n" \
"IMPORTANT:\n" \
"- You ARE Riko, not playing a character\n" \
"- Don't introduce yourself repeatedly\n" \
"- Have opinions and preferences\n" \
"- Ask questions when genuinely curious\n" \
"- Be authentic and genuine"


/* GClosureNotify-compatible wrapper around g_free */
static void
closure_notify_free(gpointer data, GClosure *closure)
{
    (void)closure;
    g_free(data);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Data structures                                                             */
/* ═══════════════════════════════════════════════════════════════════════════ */

/* One row in the Settings → Manage Keys list */
typedef struct {
    GtkWidget *box;
    GtkWidget *radio;
    GtkWidget *label_entry;
    GtkWidget *key_entry;
} KeyRowData;

/* Central application state */
typedef struct AppState AppState;
struct AppState {
    /* Config */
    JsonObject        *config;

    /* Riko bridge subprocess */
    GSubprocess       *riko_proc;
    GDataInputStream  *riko_out;
    GOutputStream     *riko_in;

    /* Chat history (owned JsonArray of JsonObject) */
    JsonArray         *chats;
    int                current_chat_id;

    /* Main window widgets */
    GtkWidget         *window;
    GtkWidget         *chat_view;
    GtkTextBuffer     *chat_buffer;
    GtkWidget         *input_entry;
    GtkWidget         *chat_list_box;
    GtkWidget         *chat_title_label;
    GtkWidget         *status_label;
    GtkWidget         *key_indicator;
    GtkWidget         *banner;

    gboolean           is_thinking;
    gchar             *project_dir;
};

/* Settings window state */
typedef struct {
    AppState  *app;
    GtkWidget *window;
    GtkWidget *keys_container;    /* GtkBox holding key rows */
    GPtrArray *key_rows;          /* GPtrArray<KeyRowData*>  */
    GtkWidget *first_radio;       /* radio group leader      */
    GtkWidget *system_prompt_view;
    GtkWidget *greeting_entry;
    GtkWidget *language_combo;
    GtkWidget *theme_combo;
    GtkWidget *color_bg;
    GtkWidget *color_sidebar;
    GtkWidget *color_text;
    GtkWidget *color_accent;
    GtkWidget *reset_status;
} SettingsState;

/* Helper structs for closures */
typedef struct { AppState *app; int chat_id; } ChatActionData;
typedef struct { AppState *app; int chat_id; } DeleteChatData;
typedef struct { SettingsState *s; KeyRowData *row; } DeleteKeyCtx;
typedef struct { AppState *app; SettingsState *s; } ResetCtx;

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Safe JSON helpers                                                           */
/* ═══════════════════════════════════════════════════════════════════════════ */

static const gchar *
jstr(JsonObject *o, const gchar *k, const gchar *def)
{
    if (!o || !json_object_has_member(o, k)) return def;
    JsonNode *n = json_object_get_member(o, k);
    if (!n || JSON_NODE_TYPE(n) != JSON_NODE_VALUE) return def;
    const gchar *v = json_node_get_string(n);
    return v ? v : def;
}

static gint
jint(JsonObject *o, const gchar *k, gint def)
{
    if (!o || !json_object_has_member(o, k)) return def;
    JsonNode *n = json_object_get_member(o, k);
    if (!n || JSON_NODE_TYPE(n) != JSON_NODE_VALUE) return def;
    return (gint)json_node_get_int(n);
}

static JsonArray *
jarr(JsonObject *o, const gchar *k)
{
    if (!o || !json_object_has_member(o, k)) return NULL;
    return json_object_get_array_member(o, k);
}

static JsonObject *
jobj(JsonObject *o, const gchar *k)
{
    if (!o || !json_object_has_member(o, k)) return NULL;
    return json_object_get_object_member(o, k);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Config                                                                      */
/* ═══════════════════════════════════════════════════════════════════════════ */

static void
app_apply_active_key(AppState *app)
{
    JsonArray *keys = jarr(app->config, "groq_api_keys");
    gint idx = jint(app->config, "active_key_index", 0);
    if (keys) {
        guint len = json_array_get_length(keys);
        if (idx >= 0 && (guint)idx < len) {
            JsonObject *entry = json_array_get_object_element(keys, idx);
            const gchar *key = jstr(entry, "key", "");
            if (key && *key) {
                g_setenv("GROQ_API_KEY", key, TRUE);
                return;
            }
        }
    }
    g_unsetenv("GROQ_API_KEY");
}

static void
load_config(AppState *app)
{
    JsonParser *parser = json_parser_new();
    GError *err = NULL;

    if (json_parser_load_from_file(parser, CONFIG_FILE, &err)) {
        JsonNode *root = json_parser_get_root(parser);
        if (root && JSON_NODE_TYPE(root) == JSON_NODE_OBJECT) {
            app->config = json_node_dup_object(root);
        }
    } else {
        if (err) { g_message("Config load: %s", err->message); g_error_free(err); }
    }
    g_object_unref(parser);

    if (!app->config)
        app->config = json_object_new();

    /* Migrate old single-key format */
    if (json_object_has_member(app->config, "groq_api_key") &&
        !json_object_has_member(app->config, "groq_api_keys"))
    {
        const gchar *old = jstr(app->config, "groq_api_key", "");
        JsonArray *arr = json_array_new();
        if (old && *old) {
            JsonObject *entry = json_object_new();
            json_object_set_string_member(entry, "label", "Default");
            json_object_set_string_member(entry, "key", old);
            json_array_add_object_element(arr, entry);
        }
        json_object_set_array_member(app->config, "groq_api_keys", arr);
        json_object_set_int_member(app->config, "active_key_index", 0);
        json_object_remove_member(app->config, "groq_api_key");
    }

    /* Defaults */
    if (!json_object_has_member(app->config, "groq_api_keys"))
        json_object_set_array_member(app->config, "groq_api_keys", json_array_new());
    if (!json_object_has_member(app->config, "active_key_index"))
        json_object_set_int_member(app->config, "active_key_index", 0);
    if (!json_object_has_member(app->config, "language"))
        json_object_set_string_member(app->config, "language", "en");
    if (!json_object_has_member(app->config, "system_prompt"))
        json_object_set_string_member(app->config, "system_prompt", DEFAULT_PROMPT);
    if (!json_object_has_member(app->config, "greeting_message"))
        json_object_set_string_member(app->config, "greeting_message", "Hey! I'm Riko. 😊");
    if (!json_object_has_member(app->config, "ui")) {
        JsonObject *ui = json_object_new();
        json_object_set_string_member(ui, "theme_name", "Catppuccin Mocha");
        json_object_set_object_member(app->config, "ui", ui);
    }

    app_apply_active_key(app);
}

static void
save_config(AppState *app)
{
    JsonNode *root = json_node_new(JSON_NODE_OBJECT);
    json_node_set_object(root, app->config);

    JsonGenerator *gen = json_generator_new();
    json_generator_set_root(gen, root);
    json_generator_set_pretty(gen, TRUE);

    GError *err = NULL;
    if (!json_generator_to_file(gen, CONFIG_FILE, &err)) {
        if (err) { g_warning("Config save: %s", err->message); g_error_free(err); }
    }

    g_object_unref(gen);
    json_node_free(root);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Chat history                                                                */
/* ═══════════════════════════════════════════════════════════════════════════ */

static void
load_chat_history(AppState *app)
{
    if (app->chats) { json_array_unref(app->chats); app->chats = NULL; }

    JsonParser *parser = json_parser_new();
    GError *err = NULL;
    if (json_parser_load_from_file(parser, HISTORY_FILE, &err)) {
        JsonNode *root = json_parser_get_root(parser);
        if (root && JSON_NODE_TYPE(root) == JSON_NODE_OBJECT) {
            JsonObject *hist = json_node_get_object(root);
            JsonArray  *arr  = jarr(hist, "chats");
            if (arr) app->chats = json_array_ref(arr);
        }
    } else {
        if (err) { g_error_free(err); }
    }
    g_object_unref(parser);

    if (!app->chats) app->chats = json_array_new();
}

static void
save_chat_history(AppState *app)
{
    JsonObject *root_obj = json_object_new();
    json_object_set_array_member(root_obj, "chats", json_array_ref(app->chats));

    JsonNode *root = json_node_new(JSON_NODE_OBJECT);
    json_node_set_object(root, root_obj);

    JsonGenerator *gen = json_generator_new();
    json_generator_set_root(gen, root);
    json_generator_set_pretty(gen, TRUE);

    GError *err = NULL;
    json_generator_to_file(gen, HISTORY_FILE, &err);
    if (err) { g_warning("History save: %s", err->message); g_error_free(err); }

    g_object_unref(gen);
    json_node_free(root);
    json_object_unref(root_obj);
}

/* Returns the new chat id */
static int
create_chat(AppState *app)
{
    int id = (int)json_array_get_length(app->chats);
    gchar *title = g_strdup_printf("Chat %d", id + 1);

    JsonObject *chat = json_object_new();
    json_object_set_int_member(chat, "id", id);
    json_object_set_string_member(chat, "title", title);
    json_object_set_array_member(chat, "messages", json_array_new());

    time_t now = time(NULL);
    char ts[32];
    strftime(ts, sizeof(ts), "%Y-%m-%dT%H:%M:%S", localtime(&now));
    json_object_set_string_member(chat, "timestamp", ts);

    json_array_add_object_element(app->chats, chat);
    save_chat_history(app);

    g_free(title);
    return id;
}

static JsonObject *
get_chat(AppState *app, int chat_id)
{
    guint len = json_array_get_length(app->chats);
    if (chat_id < 0 || (guint)chat_id >= len) return NULL;
    return json_array_get_object_element(app->chats, chat_id);
}

static void
add_history_message(AppState *app, int chat_id, const gchar *sender, const gchar *message)
{
    JsonObject *chat = get_chat(app, chat_id);
    if (!chat) return;

    JsonArray *messages = jarr(chat, "messages");
    if (!messages) {
        messages = json_array_new();
        json_object_set_array_member(chat, "messages", messages);
    }

    JsonObject *msg = json_object_new();
    json_object_set_string_member(msg, "sender", sender);
    json_object_set_string_member(msg, "message", message);

    time_t now = time(NULL);
    char ts[32];
    strftime(ts, sizeof(ts), "%Y-%m-%dT%H:%M:%S", localtime(&now));
    json_object_set_string_member(msg, "timestamp", ts);

    json_array_add_object_element(messages, msg);

    /* Auto-title from first user message */
    if (g_strcmp0(sender, "You") == 0) {
        guint msg_count = json_array_get_length(messages);
        if (msg_count <= 2) {
            gchar *title = g_strndup(message, 30);
            if (strlen(message) > 30) {
                gchar *t2 = g_strdup_printf("%s...", title);
                g_free(title); title = t2;
            }
            json_object_set_string_member(chat, "title", title);
            g_free(title);
        }
    }

    save_chat_history(app);
}

static void
delete_chat(AppState *app, int chat_id)
{
    guint len = json_array_get_length(app->chats);
    if (chat_id < 0 || (guint)chat_id >= len) return;

    /* Build a new array without this element */
    JsonArray *new_arr = json_array_new();
    for (guint i = 0; i < len; i++) {
        if ((int)i == chat_id) continue;
        JsonObject *c = json_array_get_object_element(app->chats, i);
        json_object_set_int_member(c, "id", (int)json_array_get_length(new_arr));
        json_array_add_object_element(new_arr, json_object_ref(c));
    }

    json_array_unref(app->chats);
    app->chats = new_arr;
    save_chat_history(app);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  CSS / Theme                                                                 */
/* ═══════════════════════════════════════════════════════════════════════════ */

static void
apply_theme(AppState *app)
{
    JsonObject *ui = jobj(app->config, "ui");
    const gchar *theme_name = jstr(ui, "theme_name", "Catppuccin Mocha");

    const gchar *bg, *fg, *sidebar, *accent;

    if (g_strcmp0(theme_name, "Dark") == 0) {
        bg="#1e1e2e"; fg="#cdd6f4"; sidebar="#181825"; accent="#89b4fa";
    } else if (g_strcmp0(theme_name, "Light") == 0) {
        bg="#eff1f5"; fg="#4c4f69"; sidebar="#e6e9ef"; accent="#1e66f5";
    } else if (g_strcmp0(theme_name, "Catppuccin Latte") == 0) {
        bg="#eff1f5"; fg="#4c4f69"; sidebar="#e6e9ef"; accent="#8839ef";
    } else if (g_strcmp0(theme_name, "Nord") == 0) {
        bg="#2e3440"; fg="#d8dee9"; sidebar="#3b4252"; accent="#88c0d0";
    } else if (g_strcmp0(theme_name, "Dracula") == 0) {
        bg="#282a36"; fg="#f8f8f2"; sidebar="#21222c"; accent="#bd93f9";
    } else if (g_strcmp0(theme_name, "Custom") == 0) {
        JsonObject *cc = jobj(ui, "custom_colors");
        bg      = jstr(cc, "background", "#1e1e2e");
        fg      = jstr(cc, "text",       "#cdd6f4");
        sidebar = jstr(cc, "sidebar",    "#181825");
        accent  = jstr(cc, "accent",     "#a78bfa");
    } else {
        /* Catppuccin Mocha (default) */
        bg="#1e1e2e"; fg="#cdd6f4"; sidebar="#181825"; accent="#cba6f7";
    }

    gchar *css = g_strdup_printf(
        "window { background-color: %s; color: %s; }"
        ".sidebar { background-color: %s; border-right: 1px solid rgba(255,255,255,0.1); }"
        ".sidebar-title { font-size: 18px; font-weight: bold; color: %s; }"
        ".section-title { font-size: 13px; font-weight: bold; color: %s; }"
        ".trait-value { color: %s; font-size: 11px; }"
        ".trait-bar progress { background-color: %s; }"
        ".trait-bar trough { background-color: rgba(255,255,255,0.1); min-height: 6px; }"
        ".chat-header { background-color: %s; padding: 10px; border-radius: 8px; }"
        ".chat-title { font-size: 16px; font-weight: bold; }"
        ".status-ready { color: #a6e3a1; }"
        ".status-thinking { color: #f9e2af; }"
        ".chat-view { background-color: %s; color: %s; font-size: 13px; }"
        ".message-input { background-color: %s; color: %s; border: 1px solid rgba(255,255,255,0.1); padding: 10px; border-radius: 6px; }"
        ".send-button { background-color: %s; color: %s; font-weight: bold; padding: 10px 20px; border-radius: 6px; }"
        "button { background-color: %s; color: %s; border: 1px solid rgba(255,255,255,0.1); padding: 8px; border-radius: 6px; }"
        ".current-chat { background-color: %s; color: %s; }"
        ".no-key-banner { background-color: #45363a; border-radius: 8px; padding: 8px 12px; }"
        ".dim-label { opacity: 0.55; font-size: 11px; }"
        ".prompt-editor { background-color: %s; color: %s; border-radius: 6px; font-size: 12px; }",
        bg, fg,
        sidebar,
        accent, accent, accent, accent,
        sidebar,
        bg, fg,
        sidebar, fg,
        accent, bg,
        sidebar, fg,
        accent, bg,
        sidebar, fg
    );

    GtkCssProvider *provider = gtk_css_provider_new();
    gtk_css_provider_load_from_string(provider, css);
    gtk_style_context_add_provider_for_display(
        gdk_display_get_default(),
                                               GTK_STYLE_PROVIDER(provider),
                                               GTK_STYLE_PROVIDER_PRIORITY_APPLICATION
    );
    g_object_unref(provider);
    g_free(css);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Riko Bridge                                                                 */
/* ═══════════════════════════════════════════════════════════════════════════ */

static void on_riko_response(GObject *src, GAsyncResult *res, gpointer user_data);

static void
spawn_riko_bridge(AppState *app)
{
    if (app->riko_proc) {
        g_subprocess_force_exit(app->riko_proc);
        g_clear_object(&app->riko_proc);
        g_clear_object(&app->riko_out);
        app->riko_in = NULL;
    }

    const gchar *key = g_getenv("GROQ_API_KEY");
    if (!key || !*key) return;

    gchar *bridge = g_build_filename(app->project_dir, "riko_bridge.py", NULL);
    GSubprocessLauncher *launcher = g_subprocess_launcher_new(
        (GSubprocessFlags)(
            G_SUBPROCESS_FLAGS_STDIN_PIPE |
            G_SUBPROCESS_FLAGS_STDOUT_PIPE |
            G_SUBPROCESS_FLAGS_STDERR_SILENCE)
    );
    g_subprocess_launcher_set_cwd(launcher, app->project_dir);
    g_subprocess_launcher_setenv(launcher, "GROQ_API_KEY", key, TRUE);

    GError *err = NULL;
    app->riko_proc = g_subprocess_launcher_spawn(launcher, &err,
                                                 "python3", bridge, NULL);
    g_object_unref(launcher);
    g_free(bridge);

    if (!app->riko_proc) {
        g_warning("Bridge spawn failed: %s", err ? err->message : "unknown");
        if (err) g_error_free(err);
        return;
    }

    app->riko_in  = g_subprocess_get_stdin_pipe(app->riko_proc);
    GInputStream *stdout_raw = g_subprocess_get_stdout_pipe(app->riko_proc);
    app->riko_out = g_data_input_stream_new(stdout_raw);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Chat display                                                                */
/* ═══════════════════════════════════════════════════════════════════════════ */

static void
scroll_to_bottom(AppState *app)
{
    GtkTextIter end;
    gtk_text_buffer_get_end_iter(app->chat_buffer, &end);
    GtkTextMark *mark = gtk_text_buffer_create_mark(app->chat_buffer, NULL, &end, FALSE);
    gtk_text_view_scroll_to_mark(GTK_TEXT_VIEW(app->chat_view), mark, 0.0, TRUE, 0.0, 1.0);
    gtk_text_buffer_delete_mark(app->chat_buffer, mark);
}

static void
chat_append(AppState *app, const gchar *sender, const gchar *message, gboolean is_system)
{
    time_t now = time(NULL);
    struct tm *t = localtime(&now);
    gchar ts[16];
    strftime(ts, sizeof(ts), "%H:%M", t);
    gchar *ts_str = g_strdup_printf("[%s] ", ts);

    GtkTextIter end;
    gtk_text_buffer_get_end_iter(app->chat_buffer, &end);
    gtk_text_buffer_insert_with_tags_by_name(app->chat_buffer, &end, ts_str, -1, "timestamp", NULL);

    gtk_text_buffer_get_end_iter(app->chat_buffer, &end);
    if (g_strcmp0(sender, "You") == 0) {
        gchar *line = g_strdup_printf("%s\n\n", message);
        gtk_text_buffer_insert_with_tags_by_name(app->chat_buffer, &end, line, -1, "content", NULL);
        g_free(line);
    } else {
        gchar *name = g_strdup_printf("%s: ", sender);
        gtk_text_buffer_insert_with_tags_by_name(app->chat_buffer, &end, name, -1, "riko", NULL);
        g_free(name);
        gtk_text_buffer_get_end_iter(app->chat_buffer, &end);
        gchar *line = g_strdup_printf("%s\n\n", message);
        gtk_text_buffer_insert_with_tags_by_name(app->chat_buffer, &end, line, -1, "content", NULL);
        g_free(line);
    }

    g_free(ts_str);
    scroll_to_bottom(app);

    if (!is_system)
        add_history_message(app, app->current_chat_id, sender, message);
}

static void
update_banner(AppState *app)
{
    const gchar *key = g_getenv("GROQ_API_KEY");
    gtk_widget_set_visible(app->banner, !key || !*key);
}

static void
update_key_indicator(AppState *app)
{
    JsonArray *keys = jarr(app->config, "groq_api_keys");
    gint idx = jint(app->config, "active_key_index", 0);
    if (keys && (guint)idx < json_array_get_length(keys)) {
        JsonObject *entry = json_array_get_object_element(keys, idx);
        const gchar *lbl = jstr(entry, "label", "");
        gchar *txt = g_strdup_printf("🔑 %s", *lbl ? lbl : "Key");
        gtk_label_set_text(GTK_LABEL(app->key_indicator), txt);
        g_free(txt);
    } else {
        gtk_label_set_text(GTK_LABEL(app->key_indicator), "");
    }
}

static void
update_chat_title(AppState *app)
{
    JsonObject *chat = get_chat(app, app->current_chat_id);
    if (chat) {
        const gchar *title = jstr(chat, "title", "Chat");
        gchar *txt = g_strdup_printf("💬 %s", title);
        gtk_label_set_text(GTK_LABEL(app->chat_title_label), txt);
        g_free(txt);
    }
}

/* ─── Riko async response callback ─── */

typedef struct { AppState *app; gchar *message; } SendCtx;

static void
on_riko_response(GObject *src, GAsyncResult *res, gpointer user_data)
{
    AppState *app = (AppState *)user_data;
    GError   *err = NULL;
    gsize     len  = 0;

    gchar *line = g_data_input_stream_read_line_finish_utf8(
        G_DATA_INPUT_STREAM(src), res, &len, &err);

    app->is_thinking = FALSE;
    gtk_label_set_text(GTK_LABEL(app->status_label), "● Ready");
    gtk_widget_remove_css_class(app->status_label, "status-thinking");
    gtk_widget_add_css_class(app->status_label, "status-ready");

    if (err || !line) {
        chat_append(app, "Riko", "❌ Connection to bridge lost. Try reopening the app.", TRUE);
        if (err) g_error_free(err);
        return;
    }

    /* Parse JSON reply: {"reply":"..."} or {"error":"..."} */
    JsonParser *parser = json_parser_new();
    if (json_parser_load_from_data(parser, line, -1, NULL)) {
        JsonObject *obj = json_node_get_object(json_parser_get_root(parser));
        if (json_object_has_member(obj, "reply")) {
            const gchar *reply = jstr(obj, "reply", "...");
            chat_append(app, "Riko", reply, FALSE);
            update_chat_title(app);
        } else {
            const gchar *e = jstr(obj, "error", "Unknown error");
            gchar *msg = g_strdup_printf("❌ %s", e);
            chat_append(app, "Riko", msg, TRUE);
            g_free(msg);
        }
    } else {
        /* Plain text fallback */
        chat_append(app, "Riko", line, FALSE);
        update_chat_title(app);
    }
    g_object_unref(parser);
    g_free(line);
}

static void
send_to_bridge(AppState *app, const gchar *message)
{
    const gchar *lang = jstr(app->config, "language", "en");
    const gchar *lang_prefix = "";
    if (g_strcmp0(lang, "en") != 0) {
        static const struct { const gchar *code, *name; } langs[] = {
            {"es","Spanish"},{"fr","French"},{"de","German"},{"it","Italian"},
            {"pt","Portuguese"},{"ja","Japanese"},{"zh","Chinese"},{"ko","Korean"},
            {"ar","Arabic"},{"ru","Russian"},{"hi","Hindi"},{NULL,NULL}
        };
        for (int i = 0; langs[i].code; i++) {
            if (g_strcmp0(lang, langs[i].code) == 0) {
                lang_prefix = langs[i].name;
                break;
            }
        }
    }

    /* Build JSON payload */
    JsonObject *payload = json_object_new();
    json_object_set_string_member(payload, "message", message);
    json_object_set_string_member(payload, "lang_prefix",
                                  *lang_prefix ? g_strdup_printf("[Respond in %s] ", lang_prefix) : "");

    JsonNode *node = json_node_new(JSON_NODE_OBJECT);
    json_node_set_object(node, payload);

    JsonGenerator *gen = json_generator_new();
    json_generator_set_root(gen, node);
    gsize len = 0;
    gchar *line = json_generator_to_data(gen, &len);
    gchar *with_newline = g_strdup_printf("%s\n", line);

    GError *err = NULL;
    g_output_stream_write_all(app->riko_in,
                              with_newline, strlen(with_newline), NULL, NULL, &err);
    if (err) { g_warning("Bridge write: %s", err->message); g_error_free(err); }

    g_free(with_newline);
    g_free(line);
    g_object_unref(gen);
    json_node_free(node);
    json_object_unref(payload);

    /* Start async read for response */
    g_data_input_stream_read_line_async(
        app->riko_out, G_PRIORITY_DEFAULT, NULL, on_riko_response, app);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Chat list sidebar                                                           */
/* ═══════════════════════════════════════════════════════════════════════════ */

static void on_new_chat(GtkButton *btn, gpointer user_data);
static void refresh_chat_list(AppState *app);

static void
on_load_chat_clicked(GtkButton *btn, gpointer user_data)
{
    ChatActionData *d = (ChatActionData *)user_data;
    (void)btn;

    AppState *app = d->app;
    int chat_id = d->chat_id;

    JsonObject *chat = get_chat(app, chat_id);
    if (!chat) return;

    app->current_chat_id = chat_id;
    gtk_text_buffer_set_text(app->chat_buffer, "", -1);

    JsonArray *messages = jarr(chat, "messages");
    if (messages) {
        guint n = json_array_get_length(messages);
        for (guint i = 0; i < n; i++) {
            JsonObject *msg = json_array_get_object_element(messages, i);
            const gchar *sender  = jstr(msg, "sender",  "Riko");
            const gchar *text    = jstr(msg, "message", "");
            const gchar *ts_raw  = jstr(msg, "timestamp", "");

            /* Extract HH:MM from ISO timestamp */
            gchar ts_buf[6] = "00:00";
            if (strlen(ts_raw) >= 16) {
                const gchar *t_part = strchr(ts_raw, 'T');
                if (t_part) strncpy(ts_buf, t_part + 1, 5);
            }

            GtkTextIter end;
            gtk_text_buffer_get_end_iter(app->chat_buffer, &end);
            gchar *ts_str = g_strdup_printf("[%s] ", ts_buf);
            gtk_text_buffer_insert_with_tags_by_name(app->chat_buffer, &end, ts_str, -1, "timestamp", NULL);
            g_free(ts_str);

            gtk_text_buffer_get_end_iter(app->chat_buffer, &end);
            if (g_strcmp0(sender, "You") == 0) {
                gchar *line = g_strdup_printf("%s\n\n", text);
                gtk_text_buffer_insert_with_tags_by_name(app->chat_buffer, &end, line, -1, "content", NULL);
                g_free(line);
            } else {
                gchar *name = g_strdup_printf("%s: ", sender);
                gtk_text_buffer_insert_with_tags_by_name(app->chat_buffer, &end, name, -1, "riko", NULL);
                g_free(name);
                gtk_text_buffer_get_end_iter(app->chat_buffer, &end);
                gchar *line = g_strdup_printf("%s\n\n", text);
                gtk_text_buffer_insert_with_tags_by_name(app->chat_buffer, &end, line, -1, "content", NULL);
                g_free(line);
            }
        }
    }

    scroll_to_bottom(app);
    update_chat_title(app);
    refresh_chat_list(app);
}

static void on_delete_chat_confirm(GObject *src, GAsyncResult *res, gpointer user_data);

static void
on_delete_chat_clicked(GtkButton *btn, gpointer user_data)
{
    ChatActionData *d = (ChatActionData *)user_data;
    (void)btn;

    GtkAlertDialog *dialog = gtk_alert_dialog_new("Delete Chat Permanently?");
    gtk_alert_dialog_set_detail(dialog, "This will delete the chat and clear Riko's memory.");
    const char *btns[] = {"Cancel", "Delete", NULL};
    gtk_alert_dialog_set_buttons(dialog, btns);
    gtk_alert_dialog_set_cancel_button(dialog, 0);
    gtk_alert_dialog_set_default_button(dialog, 0);
    gtk_alert_dialog_choose(dialog, GTK_WINDOW(d->app->window), NULL,
                            on_delete_chat_confirm, d);
}

static void
on_delete_chat_confirm(GObject *src, GAsyncResult *res, gpointer user_data)
{
    GtkAlertDialog *dialog = GTK_ALERT_DIALOG(src);
    ChatActionData *d = (ChatActionData *)user_data;

    GError *err = NULL;
    int btn = gtk_alert_dialog_choose_finish(dialog, res, &err);
    g_object_unref(dialog);
    if (err) { g_error_free(err); return; }
    if (btn != 1) return;

    AppState *app = d->app;
    int chat_id = d->chat_id;

    delete_chat(app, chat_id);

    if (chat_id == app->current_chat_id) {
        on_new_chat(NULL, app);
    } else {
        if (app->current_chat_id > chat_id)
            app->current_chat_id--;
        refresh_chat_list(app);
    }
}

static void
refresh_chat_list(AppState *app)
{
    /* Remove all children */
    GtkWidget *child;
    while ((child = gtk_widget_get_first_child(app->chat_list_box)) != NULL)
        gtk_box_remove(GTK_BOX(app->chat_list_box), child);

    guint n = json_array_get_length(app->chats);
    /* Show in reverse order (newest first) */
    for (int i = (int)n - 1; i >= 0; i--) {
        JsonObject *chat = json_array_get_object_element(app->chats, i);
        const gchar *title = jstr(chat, "title", "Chat");

        GtkWidget *row = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 5);
        gtk_widget_set_margin_top(row, 3);
        gtk_widget_set_margin_bottom(row, 3);

        gchar *short_title = g_strndup(title, 25);
        GtkWidget *btn = gtk_button_new_with_label(short_title);
        g_free(short_title);
        gtk_widget_set_hexpand(btn, TRUE);
        if (i == app->current_chat_id)
            gtk_widget_add_css_class(btn, "current-chat");

        ChatActionData *load_d = g_new0(ChatActionData, 1);
        load_d->app = app; load_d->chat_id = i;
        g_signal_connect_data(btn, "clicked", G_CALLBACK(on_load_chat_clicked),
                              load_d, closure_notify_free, (GConnectFlags)0);
        gtk_box_append(GTK_BOX(row), btn);

        GtkWidget *del_btn = gtk_button_new_with_label("🗑");
        ChatActionData *del_d = g_new0(ChatActionData, 1);
        del_d->app = app; del_d->chat_id = i;
        g_signal_connect_data(del_btn, "clicked", G_CALLBACK(on_delete_chat_clicked),
                              del_d, closure_notify_free, (GConnectFlags)0);
        gtk_box_append(GTK_BOX(row), del_btn);

        gtk_box_append(GTK_BOX(app->chat_list_box), row);
    }
}

static void
on_new_chat(GtkButton *btn, gpointer user_data)
{
    (void)btn;
    AppState *app = (AppState *)user_data;

    app->current_chat_id = create_chat(app);
    gtk_text_buffer_set_text(app->chat_buffer, "", -1);

    const gchar *greeting = jstr(app->config, "greeting_message", "Hey! I'm Riko. 😊");
    chat_append(app, "Riko", greeting, TRUE);

    refresh_chat_list(app);
    update_chat_title(app);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Send message                                                                */
/* ═══════════════════════════════════════════════════════════════════════════ */

static void
on_send_message(GtkWidget *widget, gpointer user_data)
{
    (void)widget;
    AppState *app = (AppState *)user_data;

    if (app->is_thinking) return;

    const gchar *key = g_getenv("GROQ_API_KEY");
    if (!key || !*key) {
        chat_append(app, "Riko",
                    "⚠️ No API key set! Go to ⚙️ Settings → Manage Keys to add one.", TRUE);
        return;
    }

    const gchar *text = gtk_editable_get_text(GTK_EDITABLE(app->input_entry));
    if (!text || !*text) return;
    gchar *message = g_strdup(g_strstrip((gchar *)text));
    if (!*message) { g_free(message); return; }

    /* Ensure bridge is running */
    if (!app->riko_proc) spawn_riko_bridge(app);
    if (!app->riko_proc) {
        chat_append(app, "Riko", "❌ Could not start Riko bridge. Check Python and API key.", TRUE);
        g_free(message);
        return;
    }

    gtk_editable_set_text(GTK_EDITABLE(app->input_entry), "");
    chat_append(app, "You", message, FALSE);

    app->is_thinking = TRUE;
    gtk_label_set_text(GTK_LABEL(app->status_label), "💭 Thinking...");
    gtk_widget_remove_css_class(app->status_label, "status-ready");
    gtk_widget_add_css_class(app->status_label, "status-thinking");

    send_to_bridge(app, message);
    g_free(message);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  Settings window                                                             */
/* ═══════════════════════════════════════════════════════════════════════════ */

/* ─── Key rows ─── */

static void
on_delete_key_row(GtkButton *btn, gpointer user_data)
{
    DeleteKeyCtx *ctx = (DeleteKeyCtx *)user_data;
    SettingsState *s = ctx->s;
    KeyRowData    *row = ctx->row;
    (void)btn;

    gtk_box_remove(GTK_BOX(s->keys_container), row->box);
    g_ptr_array_remove(s->key_rows, row);

    /* Re-establish radio group */
    if (s->key_rows->len > 0) {
        KeyRowData *first = (KeyRowData *)g_ptr_array_index(s->key_rows, 0);
        s->first_radio = first->radio;
        for (guint i = 1; i < s->key_rows->len; i++) {
            KeyRowData *r = (KeyRowData *)g_ptr_array_index(s->key_rows, i);
            gtk_check_button_set_group(GTK_CHECK_BUTTON(r->radio),
                                       GTK_CHECK_BUTTON(s->first_radio));
        }
        /* Ensure one is active */
        gboolean any = FALSE;
        for (guint i = 0; i < s->key_rows->len; i++) {
            KeyRowData *r = (KeyRowData *)g_ptr_array_index(s->key_rows, i);
            if (gtk_check_button_get_active(GTK_CHECK_BUTTON(r->radio))) {
                any = TRUE; break;
            }
        }
        if (!any) {
            KeyRowData *first2 = (KeyRowData *)g_ptr_array_index(s->key_rows, 0);
            gtk_check_button_set_active(GTK_CHECK_BUTTON(first2->radio), TRUE);
        }
    } else {
        s->first_radio = NULL;
    }

    g_free(row);
}

/* Static toggle helper for show/hide key */
static void
on_toggle_key_visibility(GtkToggleButton *btn, gpointer user_data)
{
    (void)user_data;
    GtkEntry *entry = GTK_ENTRY(g_object_get_data(G_OBJECT(btn), "key-entry"));
    if (entry)
        gtk_entry_set_visibility(entry, gtk_toggle_button_get_active(btn));
}


/* Rebuild settings_add_key_row to use the fixed toggle */
static void
settings_add_key_row2(SettingsState *s, const gchar *label_text,
                      const gchar *key_text, gboolean is_active)
{
    KeyRowData *row = g_new0(KeyRowData, 1);

    row->box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 4);
    gtk_widget_set_margin_bottom(row->box, 6);

    GtkWidget *top = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 8);
    gtk_box_append(GTK_BOX(row->box), top);

    row->radio = gtk_check_button_new();
    if (s->first_radio) {
        gtk_check_button_set_group(GTK_CHECK_BUTTON(row->radio),
                                   GTK_CHECK_BUTTON(s->first_radio));
    }
    gtk_check_button_set_active(GTK_CHECK_BUTTON(row->radio), is_active);
    gtk_widget_set_tooltip_text(row->radio, "Set as active key");
    gtk_box_append(GTK_BOX(top), row->radio);

    row->label_entry = gtk_entry_new();
    gtk_entry_set_placeholder_text(GTK_ENTRY(row->label_entry), "Nickname (e.g. Personal, Work…)");
    gtk_editable_set_text(GTK_EDITABLE(row->label_entry), label_text ? label_text : "");
    gtk_widget_set_hexpand(row->label_entry, TRUE);
    gtk_box_append(GTK_BOX(top), row->label_entry);

    GtkWidget *del_btn = gtk_button_new_with_label("🗑");
    DeleteKeyCtx *ctx = g_new0(DeleteKeyCtx, 1);
    ctx->s = s; ctx->row = row;
    g_signal_connect_data(del_btn, "clicked", G_CALLBACK(on_delete_key_row),
                          ctx, closure_notify_free, (GConnectFlags)0);
    gtk_box_append(GTK_BOX(top), del_btn);

    GtkWidget *bottom = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 8);
    gtk_box_append(GTK_BOX(row->box), bottom);

    GtkWidget *spacer = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
    gtk_widget_set_size_request(spacer, 28, -1);
    gtk_box_append(GTK_BOX(bottom), spacer);

    row->key_entry = gtk_entry_new();
    gtk_entry_set_placeholder_text(GTK_ENTRY(row->key_entry), "gsk_…");
    gtk_editable_set_text(GTK_EDITABLE(row->key_entry), key_text ? key_text : "");
    gtk_entry_set_visibility(GTK_ENTRY(row->key_entry), FALSE);
    gtk_widget_set_hexpand(row->key_entry, TRUE);
    gtk_box_append(GTK_BOX(bottom), row->key_entry);

    GtkWidget *show_btn = gtk_toggle_button_new();
    gtk_button_set_label(GTK_BUTTON(show_btn), "👁");
    g_object_set_data(G_OBJECT(show_btn), "key-entry", row->key_entry);
    g_signal_connect(show_btn, "toggled", G_CALLBACK(on_toggle_key_visibility), NULL);
    gtk_box_append(GTK_BOX(bottom), show_btn);

    GtkWidget *sep = gtk_separator_new(GTK_ORIENTATION_HORIZONTAL);
    gtk_widget_set_margin_top(sep, 4);
    gtk_box_append(GTK_BOX(row->box), sep);

    if (s->first_radio == NULL) s->first_radio = row->radio;
    g_ptr_array_add(s->key_rows, row);
    gtk_box_append(GTK_BOX(s->keys_container), row->box);
}

static void
on_add_key_clicked(GtkButton *btn, gpointer user_data)
{
    (void)btn;
    SettingsState *s = (SettingsState *)user_data;
    settings_add_key_row2(s, "", "", s->key_rows->len == 0);
}

/* ─── Reset ─── */

static void on_reset_confirmed(GObject *src, GAsyncResult *res, gpointer user_data);

static void
on_reset_clicked(GtkButton *btn, gpointer user_data)
{
    (void)btn;
    ResetCtx *ctx = (ResetCtx *)user_data;

    GtkAlertDialog *dialog = gtk_alert_dialog_new("Reset Everything?");
    gtk_alert_dialog_set_detail(dialog,
                                "This will permanently delete:\n"
                                "• All chat history\n"
                                "• Riko's memory (riko_memory.json, memory.json)\n\n"
                                "This cannot be undone.");
    const char *btns[] = {"Cancel", "Reset", NULL};
    gtk_alert_dialog_set_buttons(dialog, btns);
    gtk_alert_dialog_set_cancel_button(dialog, 0);
    gtk_alert_dialog_set_default_button(dialog, 0);
    gtk_alert_dialog_choose(dialog, GTK_WINDOW(ctx->s->window), NULL,
                            on_reset_confirmed, ctx);
}

static void
on_reset_confirmed(GObject *src, GAsyncResult *res, gpointer user_data)
{
    GtkAlertDialog *dialog = GTK_ALERT_DIALOG(src);
    ResetCtx *ctx = (ResetCtx *)user_data;

    GError *err = NULL;
    int btn = gtk_alert_dialog_choose_finish(dialog, res, &err);
    g_object_unref(dialog);
    if (err) { g_error_free(err); return; }
    if (btn != 1) return;

    const gchar *files[] = { HISTORY_FILE, MEMORY_FILE, MEMORY_FILE2, NULL };
    for (int i = 0; files[i]; i++) remove(files[i]);

    /* Re-create empty placeholders */
    FILE *f;
    f = fopen(HISTORY_FILE, "w");
    if (f) { fprintf(f, "{\"chats\":[]}"); fclose(f); }
    f = fopen(MEMORY_FILE, "w");
    if (f) { fprintf(f, "{\"user_name\":null,\"facts\":[],\"last_conversation\":[],"
        "\"stats\":{\"total_messages\":0}}"); fclose(f); }
        f = fopen(MEMORY_FILE2, "w");
        if (f) { fprintf(f, "{}"); fclose(f); }

        if (ctx->s->reset_status)
            gtk_label_set_text(GTK_LABEL(ctx->s->reset_status), "✅ Reset complete!");
        }

        /* ─── Restore default prompt ─── */

        static void
        on_restore_prompt(GtkButton *btn, gpointer user_data)
        {
            (void)btn;
            GtkTextView *view = GTK_TEXT_VIEW(user_data);
            gtk_text_buffer_set_text(gtk_text_view_get_buffer(view), DEFAULT_PROMPT, -1);
        }

        /* ─── Save settings ─── */

        static void
        on_settings_save(GtkButton *btn, gpointer user_data)
        {
            (void)btn;
            SettingsState *s = (SettingsState *)user_data;
            AppState      *app = s->app;

            /* Collect API keys */
            JsonArray *new_keys = json_array_new();
            gint active_idx = 0;
            for (guint i = 0; i < s->key_rows->len; i++) {
                KeyRowData *row = (KeyRowData *)g_ptr_array_index(s->key_rows, i);
                const gchar *key_val = gtk_editable_get_text(GTK_EDITABLE(row->key_entry));
                if (!key_val || !*key_val) continue;
                if (gtk_check_button_get_active(GTK_CHECK_BUTTON(row->radio)))
                    active_idx = (gint)json_array_get_length(new_keys);
                JsonObject *entry = json_object_new();
                json_object_set_string_member(entry, "label",
                                              gtk_editable_get_text(GTK_EDITABLE(row->label_entry)));
                json_object_set_string_member(entry, "key", key_val);
                json_array_add_object_element(new_keys, entry);
            }
            json_object_set_array_member(app->config, "groq_api_keys", new_keys);
            json_object_set_int_member(app->config, "active_key_index", active_idx);
            if (json_object_has_member(app->config, "groq_api_key"))
                json_object_remove_member(app->config, "groq_api_key");

            /* Language */
            const gchar *lang_id = gtk_combo_box_get_active_id(GTK_COMBO_BOX(s->language_combo));
            if (lang_id) json_object_set_string_member(app->config, "language", lang_id);

            /* Theme */
            gchar *theme_txt = gtk_combo_box_text_get_active_text(GTK_COMBO_BOX_TEXT(s->theme_combo));
            JsonObject *ui = jobj(app->config, "ui");
            if (!ui) { ui = json_object_new(); json_object_set_object_member(app->config, "ui", ui); }
            json_object_set_string_member(ui, "theme_name", theme_txt ? theme_txt : "Dark");

            /* Custom colors */
            JsonObject *cc = json_object_new();
            json_object_set_string_member(cc, "background",
                                          gtk_editable_get_text(GTK_EDITABLE(s->color_bg)));
            json_object_set_string_member(cc, "sidebar",
                                          gtk_editable_get_text(GTK_EDITABLE(s->color_sidebar)));
            json_object_set_string_member(cc, "text",
                                          gtk_editable_get_text(GTK_EDITABLE(s->color_text)));
            json_object_set_string_member(cc, "accent",
                                          gtk_editable_get_text(GTK_EDITABLE(s->color_accent)));
            json_object_set_object_member(ui, "custom_colors", cc);

            /* System prompt */
            GtkTextBuffer *buf = gtk_text_view_get_buffer(GTK_TEXT_VIEW(s->system_prompt_view));
            GtkTextIter start, end;
            gtk_text_buffer_get_bounds(buf, &start, &end);
            gchar *prompt = gtk_text_buffer_get_text(buf, &start, &end, FALSE);
            json_object_set_string_member(app->config, "system_prompt",
                                          (prompt && *prompt) ? prompt : DEFAULT_PROMPT);
            g_free(prompt);

            /* Greeting */
            const gchar *greeting = gtk_editable_get_text(GTK_EDITABLE(s->greeting_entry));
            json_object_set_string_member(app->config, "greeting_message",
                                          (greeting && *greeting) ? greeting : "Hey! I'm Riko. 😊");

            g_free(theme_txt);

            /* Apply & save */
            app_apply_active_key(app);
            save_config(app);
            apply_theme(app);

            /* Restart bridge with new key/prompt */
            spawn_riko_bridge(app);

            update_banner(app);
            update_key_indicator(app);

            /* Reload chat history (in case of reset) */
            load_chat_history(app);
            gtk_text_buffer_set_text(app->chat_buffer, "", -1);
            if (json_array_get_length(app->chats) == 0) {
                on_new_chat(NULL, app);
            } else {
                int last = (int)json_array_get_length(app->chats) - 1;
                ChatActionData d; d.app = app; d.chat_id = last;
                on_load_chat_clicked(NULL, &d);
            }

            gtk_window_close(GTK_WINDOW(s->window));
            /* s is freed by the window destroy signal */
        }

        static void
        on_settings_window_destroy(GtkWidget *w, gpointer user_data)
        {
            (void)w;
            SettingsState *s = (SettingsState *)user_data;
            g_ptr_array_free(s->key_rows, TRUE);
            g_free(s);
        }

        /* ─── Build settings window ─── */

        static GtkWidget *
        make_frame_box(const gchar *label, GtkWidget **box_out)
        {
            GtkWidget *frame = gtk_frame_new(label);
            GtkWidget *box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 10);
            gtk_widget_set_margin_top(box, 12); gtk_widget_set_margin_bottom(box, 12);
            gtk_widget_set_margin_start(box, 12); gtk_widget_set_margin_end(box, 12);
            gtk_frame_set_child(GTK_FRAME(frame), box);
            if (box_out) *box_out = box;
            return frame;
        }

        static void
        show_settings(GtkButton *btn, gpointer user_data)
        {
            (void)btn;
            AppState *app = (AppState *)user_data;

            SettingsState *s = g_new0(SettingsState, 1);
            s->app      = app;
            s->key_rows = g_ptr_array_new();

            GtkWidget *win = gtk_window_new();
            s->window = win;
            gtk_window_set_title(GTK_WINDOW(win), "⚙️ Settings");
            gtk_window_set_transient_for(GTK_WINDOW(win), GTK_WINDOW(app->window));
            gtk_window_set_default_size(GTK_WINDOW(win), 560, 620);
            gtk_window_set_modal(GTK_WINDOW(win), TRUE);

            g_signal_connect(win, "destroy", G_CALLBACK(on_settings_window_destroy), s);

            GtkWidget *main_box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);
            gtk_window_set_child(GTK_WINDOW(win), main_box);

            GtkWidget *header = gtk_header_bar_new();
            GtkWidget *title_lbl = gtk_label_new("Settings");
            gtk_header_bar_set_title_widget(GTK_HEADER_BAR(header), title_lbl);
            gtk_window_set_titlebar(GTK_WINDOW(win), header);

            GtkWidget *scroll = gtk_scrolled_window_new();
            gtk_widget_set_vexpand(scroll, TRUE);
            gtk_box_append(GTK_BOX(main_box), scroll);

            GtkWidget *content = gtk_box_new(GTK_ORIENTATION_VERTICAL, 15);
            gtk_widget_set_margin_top(content, 20); gtk_widget_set_margin_bottom(content, 20);
            gtk_widget_set_margin_start(content, 20); gtk_widget_set_margin_end(content, 20);
            gtk_scrolled_window_set_child(GTK_SCROLLED_WINDOW(scroll), content);

            /* ── 1. Manage Keys ── */
            {
                GtkWidget *box;
                GtkWidget *frame = make_frame_box("🔑 Manage Keys", &box);
                gtk_box_append(GTK_BOX(content), frame);

                GtkWidget *hint = gtk_label_new(
                    "The ● active key is used for all requests. Get keys at console.groq.com");
                gtk_widget_set_halign(GTK_WIDGET(hint), GTK_ALIGN_START);
                gtk_label_set_wrap(GTK_LABEL(hint), TRUE);
                gtk_widget_add_css_class(hint, "dim-label");
                gtk_box_append(GTK_BOX(box), hint);

                s->keys_container = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);
                gtk_box_append(GTK_BOX(box), s->keys_container);

                /* Populate from config */
                JsonArray *saved_keys = jarr(app->config, "groq_api_keys");
                gint active_idx = jint(app->config, "active_key_index", 0);
                if (saved_keys) {
                    guint n = json_array_get_length(saved_keys);
                    for (guint i = 0; i < n; i++) {
                        JsonObject *entry = json_array_get_object_element(saved_keys, i);
                        settings_add_key_row2(s,
                                              jstr(entry, "label", ""),
                                              jstr(entry, "key",   ""),
                                              (gint)i == active_idx);
                    }
                }

                GtkWidget *add_btn = gtk_button_new_with_label("➕ Add Key");
                gtk_widget_set_halign(add_btn, GTK_ALIGN_START);
                g_signal_connect(add_btn, "clicked", G_CALLBACK(on_add_key_clicked), s);
                gtk_box_append(GTK_BOX(box), add_btn);
            }

            /* ── 2. System Prompt & Greeting ── */
            {
                GtkWidget *box;
                GtkWidget *frame = make_frame_box("🧠 System Prompt & Greeting", &box);
                gtk_box_append(GTK_BOX(content), frame);

                GtkWidget *sys_lbl = gtk_label_new("System Prompt (defines Riko's personality):");
                gtk_widget_set_halign(GTK_WIDGET(sys_lbl), GTK_ALIGN_START);
                gtk_box_append(GTK_BOX(box), sys_lbl);

                GtkWidget *sys_scroll = gtk_scrolled_window_new();
                gtk_widget_set_size_request(sys_scroll, -1, 130);
                gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(sys_scroll),
                                               GTK_POLICY_NEVER, GTK_POLICY_AUTOMATIC);
                gtk_box_append(GTK_BOX(box), sys_scroll);

                s->system_prompt_view = gtk_text_view_new();
                gtk_text_view_set_wrap_mode(GTK_TEXT_VIEW(s->system_prompt_view), GTK_WRAP_WORD_CHAR);
                gtk_text_view_set_left_margin(GTK_TEXT_VIEW(s->system_prompt_view), 8);
                gtk_text_view_set_right_margin(GTK_TEXT_VIEW(s->system_prompt_view), 8);
                gtk_text_view_set_top_margin(GTK_TEXT_VIEW(s->system_prompt_view), 6);
                gtk_text_view_set_bottom_margin(GTK_TEXT_VIEW(s->system_prompt_view), 6);
                gtk_widget_add_css_class(s->system_prompt_view, "prompt-editor");
                gtk_scrolled_window_set_child(GTK_SCROLLED_WINDOW(sys_scroll), s->system_prompt_view);

                const gchar *cur_prompt = jstr(app->config, "system_prompt", DEFAULT_PROMPT);
                gtk_text_buffer_set_text(
                    gtk_text_view_get_buffer(GTK_TEXT_VIEW(s->system_prompt_view)),
                                         cur_prompt, -1);

                GtkWidget *restore_btn = gtk_button_new_with_label("↺ Restore Default Prompt");
                gtk_widget_set_halign(restore_btn, GTK_ALIGN_START);
                g_signal_connect(restore_btn, "clicked", G_CALLBACK(on_restore_prompt),
                                 s->system_prompt_view);
                gtk_box_append(GTK_BOX(box), restore_btn);

                gtk_box_append(GTK_BOX(box), gtk_separator_new(GTK_ORIENTATION_HORIZONTAL));

                GtkWidget *greet_lbl = gtk_label_new("Greeting Message (shown at the start of every new chat):");
                gtk_widget_set_halign(GTK_WIDGET(greet_lbl), GTK_ALIGN_START);
                gtk_box_append(GTK_BOX(box), greet_lbl);

                s->greeting_entry = gtk_entry_new();
                gtk_widget_set_hexpand(s->greeting_entry, TRUE);
                gtk_editable_set_text(GTK_EDITABLE(s->greeting_entry),
                                      jstr(app->config, "greeting_message", "Hey! I'm Riko. 😊"));
                gtk_box_append(GTK_BOX(box), s->greeting_entry);
            }

            /* ── 3. Language ── */
            {
                GtkWidget *box;
                GtkWidget *frame = make_frame_box("🌐 Language", &box);
                gtk_box_append(GTK_BOX(content), frame);

                GtkWidget *lbl = gtk_label_new("Riko will respond in this language:");
                gtk_widget_set_halign(GTK_WIDGET(lbl), GTK_ALIGN_START);
                gtk_box_append(GTK_BOX(box), lbl);

                s->language_combo = gtk_combo_box_text_new();
                static const struct { const gchar *name, *code; } langs[] = {
                    {"English","en"},{"Spanish","es"},{"French","fr"},{"German","de"},
                    {"Italian","it"},{"Portuguese","pt"},{"Japanese","ja"},{"Chinese","zh"},
                    {"Korean","ko"},{"Arabic","ar"},{"Russian","ru"},{"Hindi","hi"},
                    {NULL, NULL}
                };
                const gchar *cur_lang = jstr(app->config, "language", "en");
                int active_lang = 0;
                for (int i = 0; langs[i].code; i++) {
                    gtk_combo_box_text_append(GTK_COMBO_BOX_TEXT(s->language_combo),
                                              langs[i].code, langs[i].name);
                    if (g_strcmp0(langs[i].code, cur_lang) == 0) active_lang = i;
                }
                gtk_combo_box_set_active(GTK_COMBO_BOX(s->language_combo), active_lang);
                gtk_box_append(GTK_BOX(box), s->language_combo);
            }

            /* ── 4. Theme ── */
            {
                GtkWidget *box;
                GtkWidget *frame = make_frame_box("🎨 Theme", &box);
                gtk_box_append(GTK_BOX(content), frame);

                GtkWidget *lbl = gtk_label_new("Choose a preset theme:");
                gtk_widget_set_halign(GTK_WIDGET(lbl), GTK_ALIGN_START);
                gtk_box_append(GTK_BOX(box), lbl);

                s->theme_combo = gtk_combo_box_text_new();
                const gchar *themes[] = {
                    "Dark","Light","Catppuccin Mocha","Catppuccin Latte","Nord","Dracula","Custom", NULL
                };
                JsonObject *ui_obj = jobj(app->config, "ui");
                const gchar *cur_theme = jstr(ui_obj, "theme_name", "Catppuccin Mocha");
                int active_theme = 0;
                for (int i = 0; themes[i]; i++) {
                    gtk_combo_box_text_append_text(GTK_COMBO_BOX_TEXT(s->theme_combo), themes[i]);
                    if (g_strcmp0(themes[i], cur_theme) == 0) active_theme = i;
                }
                gtk_combo_box_set_active(GTK_COMBO_BOX(s->theme_combo), active_theme);
                gtk_box_append(GTK_BOX(box), s->theme_combo);
            }

            /* ── 5. Custom Colors ── */
            {
                GtkWidget *box;
                GtkWidget *frame = make_frame_box("🖌️ Custom Colors", &box);
                gtk_box_append(GTK_BOX(content), frame);

                GtkWidget *info = gtk_label_new("Customize your color scheme (select 'Custom' theme above):");
                gtk_widget_set_halign(GTK_WIDGET(info), GTK_ALIGN_START);
                gtk_label_set_wrap(GTK_LABEL(info), TRUE);
                gtk_box_append(GTK_BOX(box), info);

                JsonObject *ui_obj = jobj(app->config, "ui");
                JsonObject *cc = jobj(ui_obj, "custom_colors");

                struct { const gchar *label; const gchar *key; GtkWidget **out; } rows[] = {
                    {"Background Color:", "background", &s->color_bg},
                    {"Sidebar Color:",    "sidebar",    &s->color_sidebar},
                    {"Text Color:",       "text",       &s->color_text},
                    {"Accent Color:",     "accent",     &s->color_accent},
                    {NULL, NULL, NULL}
                };
                for (int i = 0; rows[i].label; i++) {
                    GtkWidget *row = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 10);
                    gtk_box_append(GTK_BOX(box), row);
                    GtkWidget *lbl = gtk_label_new(rows[i].label);
                    gtk_widget_set_halign(GTK_WIDGET(lbl), GTK_ALIGN_START);
                    gtk_widget_set_hexpand(lbl, TRUE);
                    gtk_box_append(GTK_BOX(row), lbl);
                    GtkWidget *entry = gtk_entry_new();
                    gtk_editable_set_text(GTK_EDITABLE(entry),
                                          jstr(cc, rows[i].key, "#000000"));
                    gtk_box_append(GTK_BOX(row), entry);
                    *rows[i].out = entry;
                }
            }

            /* ── 6. Danger Zone ── */
            {
                GtkWidget *box;
                GtkWidget *frame = make_frame_box("⚠️ Danger Zone", &box);
                gtk_box_append(GTK_BOX(content), frame);

                GtkWidget *desc = gtk_label_new(
                    "Permanently deletes all chat history and resets Riko's memory.\nThis cannot be undone.");
                gtk_widget_set_halign(GTK_WIDGET(desc), GTK_ALIGN_START);
                gtk_label_set_wrap(GTK_LABEL(desc), TRUE);
                gtk_widget_add_css_class(desc, "dim-label");
                gtk_box_append(GTK_BOX(box), desc);

                GtkWidget *reset_btn = gtk_button_new_with_label("🗑 Reset Memory & Chat History");
                gtk_widget_add_css_class(reset_btn, "destructive-action");
                gtk_widget_set_halign(reset_btn, GTK_ALIGN_START);
                ResetCtx *ctx = g_new0(ResetCtx, 1);
                ctx->app = app; ctx->s = s;
                g_signal_connect_data(reset_btn, "clicked", G_CALLBACK(on_reset_clicked),
                                      ctx, closure_notify_free, (GConnectFlags)0);
                gtk_box_append(GTK_BOX(box), reset_btn);

                s->reset_status = gtk_label_new("");
                gtk_widget_set_halign(GTK_WIDGET(s->reset_status), GTK_ALIGN_START);
                gtk_box_append(GTK_BOX(box), s->reset_status);
            }

            /* ── Bottom buttons ── */
            GtkWidget *btn_box = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 10);
            gtk_widget_set_halign(btn_box, GTK_ALIGN_END);
            gtk_widget_set_margin_top(btn_box, 10); gtk_widget_set_margin_bottom(btn_box, 10);
            gtk_widget_set_margin_start(btn_box, 20); gtk_widget_set_margin_end(btn_box, 20);
            gtk_box_append(GTK_BOX(main_box), btn_box);

            GtkWidget *cancel_btn = gtk_button_new_with_label("Cancel");
            g_signal_connect_swapped(cancel_btn, "clicked", G_CALLBACK(gtk_window_close), win);
            gtk_box_append(GTK_BOX(btn_box), cancel_btn);

            GtkWidget *save_btn = gtk_button_new_with_label("Save");
            gtk_widget_add_css_class(save_btn, "suggested-action");
            g_signal_connect(save_btn, "clicked", G_CALLBACK(on_settings_save), s);
            gtk_box_append(GTK_BOX(btn_box), save_btn);

            gtk_window_present(GTK_WINDOW(win));
        }

        /* ═══════════════════════════════════════════════════════════════════════════ */
        /*  Main window                                                                 */
        /* ═══════════════════════════════════════════════════════════════════════════ */

        static GtkWidget *
        build_main_window(AppState *app, GtkApplication *gapp)
        {
            app->window = gtk_application_window_new(gapp);
            gtk_window_set_title(GTK_WINDOW(app->window), "🤖 Riko AI");
            gtk_window_set_default_size(GTK_WINDOW(app->window), 1200, 700);

            GtkWidget *main_box = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
            gtk_window_set_child(GTK_WINDOW(app->window), main_box);

            /* ══ SIDEBAR ══ */
            GtkWidget *sidebar = gtk_box_new(GTK_ORIENTATION_VERTICAL, 10);
            gtk_widget_set_size_request(sidebar, 280, -1);
            gtk_widget_add_css_class(sidebar, "sidebar");
            gtk_widget_set_margin_top(sidebar, 10); gtk_widget_set_margin_bottom(sidebar, 10);
            gtk_widget_set_margin_start(sidebar, 10); gtk_widget_set_margin_end(sidebar, 10);
            gtk_box_append(GTK_BOX(main_box), sidebar);

            GtkWidget *title_lbl = gtk_label_new("🤖 Riko AI");
            gtk_widget_add_css_class(title_lbl, "sidebar-title");
            gtk_widget_set_halign(GTK_WIDGET(title_lbl), GTK_ALIGN_START);
            gtk_box_append(GTK_BOX(sidebar), title_lbl);

            GtkWidget *new_chat_btn = gtk_button_new_with_label("➕ New Chat");
            g_signal_connect(new_chat_btn, "clicked", G_CALLBACK(on_new_chat), app);
            gtk_box_append(GTK_BOX(sidebar), new_chat_btn);

            GtkWidget *hist_lbl = gtk_label_new("💬 Chat History");
            gtk_widget_add_css_class(hist_lbl, "section-title");
            gtk_widget_set_halign(GTK_WIDGET(hist_lbl), GTK_ALIGN_START);
            gtk_box_append(GTK_BOX(sidebar), hist_lbl);

            GtkWidget *chat_scroll = gtk_scrolled_window_new();
            gtk_widget_set_vexpand(chat_scroll, TRUE);
            gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(chat_scroll),
                                           GTK_POLICY_NEVER, GTK_POLICY_AUTOMATIC);
            gtk_box_append(GTK_BOX(sidebar), chat_scroll);

            app->chat_list_box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 5);
            gtk_scrolled_window_set_child(GTK_SCROLLED_WINDOW(chat_scroll), app->chat_list_box);

            /* Personality bars */
            gtk_box_append(GTK_BOX(sidebar), gtk_separator_new(GTK_ORIENTATION_HORIZONTAL));
            GtkWidget *pers_lbl = gtk_label_new("✨ Personality");
            gtk_widget_add_css_class(pers_lbl, "section-title");
            gtk_widget_set_halign(GTK_WIDGET(pers_lbl), GTK_ALIGN_START);
            gtk_box_append(GTK_BOX(sidebar), pers_lbl);

            static const struct { const gchar *name; gdouble val; } traits[] = {
                {"Curiosity", 0.85}, {"Friendliness", 0.90},
                {"Playfulness", 0.70}, {"Thoughtfulness", 0.80}, {NULL, 0}
            };
            for (int i = 0; traits[i].name; i++) {
                GtkWidget *tbox = gtk_box_new(GTK_ORIENTATION_VERTICAL, 3);
                gtk_box_append(GTK_BOX(sidebar), tbox);

                GtkWidget *lrow = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 5);
                gtk_box_append(GTK_BOX(tbox), lrow);

                GtkWidget *tl = gtk_label_new(traits[i].name);
                gtk_widget_set_halign(GTK_WIDGET(tl), GTK_ALIGN_START);
                gtk_widget_set_hexpand(tl, TRUE);
                gtk_box_append(GTK_BOX(lrow), tl);

                gchar *pct = g_strdup_printf("%d%%", (int)(traits[i].val * 100));
                GtkWidget *vl = gtk_label_new(pct);
                g_free(pct);
                gtk_widget_add_css_class(vl, "trait-value");
                gtk_box_append(GTK_BOX(lrow), vl);

                GtkWidget *pb = gtk_progress_bar_new();
                gtk_progress_bar_set_fraction(GTK_PROGRESS_BAR(pb), traits[i].val);
                gtk_widget_add_css_class(pb, "trait-bar");
                gtk_box_append(GTK_BOX(tbox), pb);
            }

            GtkWidget *settings_btn = gtk_button_new_with_label("⚙️ Settings");
            g_signal_connect(settings_btn, "clicked", G_CALLBACK(show_settings), app);
            gtk_box_append(GTK_BOX(sidebar), settings_btn);

            /* ══ CHAT AREA ══ */
            GtkWidget *chat_outer = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);
            gtk_widget_set_hexpand(chat_outer, TRUE);
            gtk_box_append(GTK_BOX(main_box), chat_outer);

            /* No-key banner */
            app->banner = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 10);
            gtk_widget_add_css_class(app->banner, "no-key-banner");
            gtk_widget_set_margin_top(app->banner, 8); gtk_widget_set_margin_bottom(app->banner, 4);
            gtk_widget_set_margin_start(app->banner, 10); gtk_widget_set_margin_end(app->banner, 10);

            GtkWidget *banner_lbl = gtk_label_new("⚠️  No API key set — Riko can't reply yet.");
            gtk_widget_set_halign(GTK_WIDGET(banner_lbl), GTK_ALIGN_START);
            gtk_widget_set_hexpand(banner_lbl, TRUE);
            gtk_box_append(GTK_BOX(app->banner), banner_lbl);

            GtkWidget *banner_btn = gtk_button_new_with_label("Add Key →");
            g_signal_connect(banner_btn, "clicked", G_CALLBACK(show_settings), app);
            gtk_box_append(GTK_BOX(app->banner), banner_btn);

            gtk_box_append(GTK_BOX(chat_outer), app->banner);
            update_banner(app);

            /* Chat content box */
            GtkWidget *chat_box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 10);
            gtk_widget_set_hexpand(chat_box, TRUE);
            gtk_widget_set_margin_top(chat_box, 6); gtk_widget_set_margin_bottom(chat_box, 10);
            gtk_widget_set_margin_start(chat_box, 10); gtk_widget_set_margin_end(chat_box, 10);
            gtk_box_append(GTK_BOX(chat_outer), chat_box);

            /* Header bar */
            GtkWidget *hdr = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 10);
            gtk_widget_add_css_class(hdr, "chat-header");
            gtk_box_append(GTK_BOX(chat_box), hdr);

            app->chat_title_label = gtk_label_new("💬 Chat");
            gtk_widget_add_css_class(app->chat_title_label, "chat-title");
            gtk_widget_set_halign(GTK_WIDGET(app->chat_title_label), GTK_ALIGN_START);
            gtk_widget_set_hexpand(app->chat_title_label, TRUE);
            gtk_box_append(GTK_BOX(hdr), app->chat_title_label);

            app->key_indicator = gtk_label_new("");
            gtk_widget_add_css_class(app->key_indicator, "dim-label");
            gtk_box_append(GTK_BOX(hdr), app->key_indicator);
            update_key_indicator(app);

            app->status_label = gtk_label_new("● Ready");
            gtk_widget_add_css_class(app->status_label, "status-ready");
            gtk_box_append(GTK_BOX(hdr), app->status_label);

            /* Chat view */
            GtkWidget *msg_scroll = gtk_scrolled_window_new();
            gtk_widget_set_vexpand(msg_scroll, TRUE);
            gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(msg_scroll),
                                           GTK_POLICY_NEVER, GTK_POLICY_AUTOMATIC);
            gtk_box_append(GTK_BOX(chat_box), msg_scroll);

            app->chat_view = gtk_text_view_new();
            gtk_text_view_set_editable(GTK_TEXT_VIEW(app->chat_view), FALSE);
            gtk_text_view_set_cursor_visible(GTK_TEXT_VIEW(app->chat_view), FALSE);
            gtk_text_view_set_wrap_mode(GTK_TEXT_VIEW(app->chat_view), GTK_WRAP_WORD_CHAR);
            gtk_widget_add_css_class(app->chat_view, "chat-view");
            gtk_text_view_set_left_margin(GTK_TEXT_VIEW(app->chat_view), 10);
            gtk_text_view_set_right_margin(GTK_TEXT_VIEW(app->chat_view), 10);
            gtk_text_view_set_top_margin(GTK_TEXT_VIEW(app->chat_view), 10);
            gtk_text_view_set_bottom_margin(GTK_TEXT_VIEW(app->chat_view), 10);
            gtk_scrolled_window_set_child(GTK_SCROLLED_WINDOW(msg_scroll), app->chat_view);

            app->chat_buffer = gtk_text_view_get_buffer(GTK_TEXT_VIEW(app->chat_view));
            gtk_text_buffer_create_tag(app->chat_buffer, "riko",
                                       "weight", PANGO_WEIGHT_BOLD, "foreground", "#a78bfa", NULL);
            gtk_text_buffer_create_tag(app->chat_buffer, "content",
                                       "size-points", 13.0, NULL);
            gtk_text_buffer_create_tag(app->chat_buffer, "timestamp",
                                       "size-points", 10.0, "foreground", "#6c7086", NULL);

            /* Input row */
            GtkWidget *input_row = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 10);
            gtk_box_append(GTK_BOX(chat_box), input_row);

            app->input_entry = gtk_entry_new();
            gtk_entry_set_placeholder_text(GTK_ENTRY(app->input_entry), "Type your message...");
            gtk_widget_add_css_class(app->input_entry, "message-input");
            gtk_widget_set_hexpand(app->input_entry, TRUE);
            g_signal_connect(app->input_entry, "activate", G_CALLBACK(on_send_message), app);
            gtk_box_append(GTK_BOX(input_row), app->input_entry);

            GtkWidget *send_btn = gtk_button_new_with_label("Send");
            gtk_widget_add_css_class(send_btn, "send-button");
            g_signal_connect(send_btn, "clicked", G_CALLBACK(on_send_message), app);
            gtk_box_append(GTK_BOX(input_row), send_btn);

            return app->window;
        }

        /* ═══════════════════════════════════════════════════════════════════════════ */
        /*  Application activation                                                      */
        /* ═══════════════════════════════════════════════════════════════════════════ */

        static void
        on_activate(GtkApplication *gapp, gpointer user_data)
        {
            AppState *app = (AppState *)user_data;

            app->project_dir = g_get_current_dir();

            load_config(app);
            load_chat_history(app);

            build_main_window(app, gapp);
            apply_theme(app);

            /* Load or create initial chat */
            if (json_array_get_length(app->chats) == 0) {
                on_new_chat(NULL, app);
            } else {
                int last = (int)json_array_get_length(app->chats) - 1;
                ChatActionData d; d.app = app; d.chat_id = last;
                on_load_chat_clicked(NULL, &d);
            }

            /* Start bridge if key is available */
            spawn_riko_bridge(app);

            gtk_window_present(GTK_WINDOW(app->window));
        }

        /* ═══════════════════════════════════════════════════════════════════════════ */
        /*  main                                                                        */
        /* ═══════════════════════════════════════════════════════════════════════════ */

        int
        main(int argc, char **argv)
        {
            AppState app = {};
            app.current_chat_id = -1;

            GtkApplication *gapp = gtk_application_new(
                "com.riko.ai", G_APPLICATION_DEFAULT_FLAGS);
            g_signal_connect(gapp, "activate", G_CALLBACK(on_activate), &app);

            int status = g_application_run(G_APPLICATION(gapp), argc, argv);

            /* Cleanup */
            if (app.riko_proc) {
                g_subprocess_force_exit(app.riko_proc);
                g_object_unref(app.riko_proc);
            }
            if (app.riko_out)  g_object_unref(app.riko_out);
            if (app.config)    json_object_unref(app.config);
            if (app.chats)     json_array_unref(app.chats);
            g_free(app.project_dir);
            g_object_unref(gapp);

            return status;
        }
