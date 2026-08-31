# Telegram Chat Cleanup Design

## Goal

Keep the private Telegram chat with the notifier from turning into an endless notification history. At bedtime, the user should be able to issue an `отбой` command and start the next day with a visually clean bot chat.

## Telegram Constraint

Telegram does not provide a "clear chat" Bot API method for arbitrary private-chat history. The bot can delete messages only by known `message_id`, and deletion is limited by Telegram's normal message deletion window. Therefore the app can reliably clean messages that it starts tracking after this feature is deployed. Older untracked history should be removed manually once.

## Command

Support both forms:

```text
/отбой
отбой
```

The plain-text form is allowed because this command is intentionally ritual-like and low-risk: it only attempts to delete tracked chat messages and then reports the result.

## Tracked Message State

Extend `data/state.json` with a `telegram_messages` list. Each item stores:

- `message_id`;
- `direction`: `incoming` or `outgoing`;
- `at`: local timestamp when the app observed or sent the message.

The app records:

- outgoing scheduled notifications;
- outgoing bot replies;
- incoming Telegram commands/messages accepted from the configured chat.

The list is capped to a small rolling window, enough for the last 48 hours plus slack. A cap of 500 message ids is enough for the current notification volume and keeps `state.json` simple.

## Cleanup Behavior

When `отбой` runs:

1. Read tracked Telegram message ids from state.
2. Delete them through Telegram Bot API in batches where possible.
3. Ignore per-message deletion failures caused by age, prior deletion, or Telegram permissions.
4. Clear successfully attempted tracked ids from state so the next day starts clean.
5. Send one final confirmation message such as:

```text
Отбой. Чат очищен: удалено 37, пропущено 2.
```

The final confirmation stays in the chat. It becomes the first tracked outgoing message for the next cleanup cycle.

## API Shape

Add Telegram client methods:

- `send_message(text) -> int | None`, returning Telegram `message_id` when available;
- `delete_messages(message_ids) -> DeleteSummary`, using `deleteMessages` for batches and falling back to `deleteMessage` if needed.

The rest of the app should call small wrapper helpers instead of calling Telegram directly when message tracking matters.

## Error Handling

If Telegram is disabled, `отбой` returns that cleanup is unavailable.

If some deletes fail, the command still completes and reports counts. Cleanup should never crash the notifier loop.

If the message tracker is empty, the bot replies that there is nothing to delete yet.

## Testing

Add tests before implementation:

- Telegram client returns `message_id` from `sendMessage`;
- Telegram client deletes ids in a batch;
- state stores and caps tracked Telegram message ids;
- scheduled notifications record outgoing Telegram message ids;
- command processing records incoming command ids and outgoing reply ids;
- `отбой` deletes tracked messages, clears old state, and sends a final confirmation.
