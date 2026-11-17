package com.yummi.restaurante.ui.products

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.yummi.restaurante.data.api.RetrofitClient
import com.yummi.restaurante.data.model.Product
import kotlinx.coroutines.launch

sealed class ProductsUiState {
    object Idle : ProductsUiState()
    object Loading : ProductsUiState()
    data class Success(val products: List<Product>) : ProductsUiState()
    data class Error(val message: String) : ProductsUiState()
}

sealed class ProductActionState {
    object Idle : ProductActionState()
    object Loading : ProductActionState()
    data class Success(val message: String) : ProductActionState()
    data class Error(val message: String) : ProductActionState()
}

class ProductsViewModel : ViewModel() {

    private val _productsState = MutableLiveData<ProductsUiState>(ProductsUiState.Idle)
    val productsState: LiveData<ProductsUiState> = _productsState

    private val _actionState = MutableLiveData<ProductActionState>(ProductActionState.Idle)
    val actionState: LiveData<ProductActionState> = _actionState

    fun loadProducts(token: String) {
        _productsState.value = ProductsUiState.Loading
        viewModelScope.launch {
            try {
                val response = RetrofitClient.api.getProducts(token)
                if (response.isSuccessful) {
                    _productsState.value = ProductsUiState.Success(
                        response.body()?.data ?: emptyList()
                    )
                } else {
                    _productsState.value = ProductsUiState.Error("Erro ao carregar produtos.")
                }
            } catch (e: Exception) {
                _productsState.value = ProductsUiState.Error("Erro de conexão.")
            }
        }
    }

    fun createProduct(token: String, product: Product) {
        _actionState.value = ProductActionState.Loading
        viewModelScope.launch {
            try {
                val response = RetrofitClient.api.createProduct(token, product)
                if (response.isSuccessful && response.body()?.success == true) {
                    _actionState.value = ProductActionState.Success("Produto criado com sucesso!")
                } else {
                    _actionState.value = ProductActionState.Error(
                        response.body()?.message ?: "Erro ao criar produto."
                    )
                }
            } catch (e: Exception) {
                _actionState.value = ProductActionState.Error("Erro de conexão.")
            }
        }
    }

    fun updateProduct(token: String, product: Product) {
        _actionState.value = ProductActionState.Loading
        viewModelScope.launch {
            try {
                val response = RetrofitClient.api.updateProduct(token, product.id, product)
                if (response.isSuccessful && response.body()?.success == true) {
                    _actionState.value = ProductActionState.Success("Produto atualizado!")
                } else {
                    _actionState.value = ProductActionState.Error(
                        response.body()?.message ?: "Erro ao atualizar produto."
                    )
                }
            } catch (e: Exception) {
                _actionState.value = ProductActionState.Error("Erro de conexão.")
            }
        }
    }

    fun deleteProduct(token: String, productId: Int) {
        _actionState.value = ProductActionState.Loading
        viewModelScope.launch {
            try {
                val response = RetrofitClient.api.deleteProduct(token, productId)
                if (response.isSuccessful) {
                    _actionState.value = ProductActionState.Success("Produto removido.")
                } else {
                    _actionState.value = ProductActionState.Error("Erro ao remover produto.")
                }
            } catch (e: Exception) {
                _actionState.value = ProductActionState.Error("Erro de conexão.")
            }
        }
    }

    fun resetActionState() {
        _actionState.value = ProductActionState.Idle
    }
}
