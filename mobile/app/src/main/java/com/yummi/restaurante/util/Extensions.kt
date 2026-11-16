package com.yummi.restaurante.util

import android.content.Context
import android.view.View
import android.widget.Toast
import com.google.android.material.snackbar.Snackbar

fun View.visible() { visibility = View.VISIBLE }
fun View.gone() { visibility = View.GONE }

fun Context.toast(msg: String) =
    Toast.makeText(this, msg, Toast.LENGTH_SHORT).show()

fun View.snack(msg: String) =
    Snackbar.make(this, msg, Snackbar.LENGTH_SHORT).show()

fun String.toBearerToken() = "Bearer $this"
