"""Tastiere Telegram per il bot."""

from __future__ import annotations

from telegram import ReplyKeyboardMarkup

MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
	[
		["Ordini", "Stato"],
		["Config", "Monitor"],
		["Annulla"],
	],
	resize_keyboard=True,
)
