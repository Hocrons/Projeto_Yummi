package com.yummi.restaurante.util

import android.content.Context
import android.content.SharedPreferences

class SessionManager(context: Context) {

    private val prefs: SharedPreferences =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    companion object {
        private const val PREFS_NAME = "yummi_session"
        private const val KEY_TOKEN = "auth_token"
        private const val KEY_RESTAURANT_ID = "restaurant_id"
        private const val KEY_NOME = "nome"
    }

    fun saveSession(token: String, restaurantId: Int, nome: String) {
        prefs.edit()
            .putString(KEY_TOKEN, token)
            .putInt(KEY_RESTAURANT_ID, restaurantId)
            .putString(KEY_NOME, nome)
            .apply()
    }

    fun getToken(): String? = prefs.getString(KEY_TOKEN, null)

    fun getRestaurantId(): Int = prefs.getInt(KEY_RESTAURANT_ID, -1)

    fun getNome(): String? = prefs.getString(KEY_NOME, null)

    fun isLoggedIn(): Boolean = getToken() != null

    fun clearSession() = prefs.edit().clear().apply()

    fun bearerToken(): String = "Bearer ${getToken()}"
}
