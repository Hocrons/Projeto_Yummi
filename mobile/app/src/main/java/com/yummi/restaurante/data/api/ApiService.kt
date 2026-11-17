package com.yummi.restaurante.data.api

import com.yummi.restaurante.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    @POST("api/restaurante/login")
    suspend fun login(@Body request: LoginRequest): Response<LoginResponse>

    @GET("api/restaurante/produtos")
    suspend fun getProducts(
        @Header("Authorization") token: String
    ): Response<ApiResponse<List<Product>>>

    @POST("api/restaurante/produtos")
    suspend fun createProduct(
        @Header("Authorization") token: String,
        @Body product: Product
    ): Response<ApiResponse<Product>>

    @PUT("api/restaurante/produtos/{id}")
    suspend fun updateProduct(
        @Header("Authorization") token: String,
        @Path("id") id: Int,
        @Body product: Product
    ): Response<ApiResponse<Product>>

    @DELETE("api/restaurante/produtos/{id}")
    suspend fun deleteProduct(
        @Header("Authorization") token: String,
        @Path("id") id: Int
    ): Response<ApiResponse<Nothing>>
}
