package com.yummi.restaurante.ui.login

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.yummi.restaurante.data.api.RetrofitClient
import com.yummi.restaurante.data.model.LoginRequest
import com.yummi.restaurante.data.model.LoginResponse
import kotlinx.coroutines.launch

sealed class LoginUiState {
    object Idle : LoginUiState()
    object Loading : LoginUiState()
    data class Success(val response: LoginResponse) : LoginUiState()
    data class Error(val message: String) : LoginUiState()
}

class LoginViewModel : ViewModel() {

    private val _uiState = MutableLiveData<LoginUiState>(LoginUiState.Idle)
    val uiState: LiveData<LoginUiState> = _uiState

    fun login(email: String, senha: String) {
        if (email.isBlank() || senha.isBlank()) {
            _uiState.value = LoginUiState.Error("Preencha e-mail e senha.")
            return
        }
        _uiState.value = LoginUiState.Loading
        viewModelScope.launch {
            try {
                val response = RetrofitClient.api.login(LoginRequest(email.trim(), senha))
                if (response.isSuccessful && response.body()?.success == true) {
                    _uiState.value = LoginUiState.Success(response.body()!!)
                } else {
                    val msg = response.body()?.message ?: "E-mail ou senha inválidos."
                    _uiState.value = LoginUiState.Error(msg)
                }
            } catch (e: Exception) {
                _uiState.value = LoginUiState.Error("Erro de conexão. Verifique o servidor.")
            }
        }
    }
}
