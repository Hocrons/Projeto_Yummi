package com.yummi.restaurante.data.model

import com.google.gson.annotations.SerializedName

data class Product(
    val id: Int = 0,
    @SerializedName("id_restaurante") val restaurantId: Int = 0,
    val nome: String = "",
    val descricao: String? = null,
    val preco: Double = 0.0,
    val disponivel: Boolean = true,
    @SerializedName("foto_url") val fotoUrl: String? = null
)
