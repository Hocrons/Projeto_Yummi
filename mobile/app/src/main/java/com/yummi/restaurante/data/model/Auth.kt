package com.yummi.restaurante.data.model

data class LoginRequest(
    val email: String,
    val senha: String
)

data class LoginResponse(
    val success: Boolean,
    val message: String? = null,
    val token: String? = null,
    val restaurantId: Int? = null,
    val nome: String? = null
)

data class ApiResponse<T>(
    val success: Boolean,
    val message: String? = null,
    val data: T? = null
)
