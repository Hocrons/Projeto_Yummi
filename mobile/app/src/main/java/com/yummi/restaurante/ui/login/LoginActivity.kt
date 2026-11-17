package com.yummi.restaurante.ui.login

import android.content.Intent
import android.os.Bundle
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import com.yummi.restaurante.databinding.ActivityLoginBinding
import com.yummi.restaurante.ui.products.ProductListActivity
import com.yummi.restaurante.util.SessionManager
import com.yummi.restaurante.util.gone
import com.yummi.restaurante.util.snack
import com.yummi.restaurante.util.visible

class LoginActivity : AppCompatActivity() {

    private lateinit var binding: ActivityLoginBinding
    private val viewModel: LoginViewModel by viewModels()
    private lateinit var session: SessionManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityLoginBinding.inflate(layoutInflater)
        setContentView(binding.root)

        session = SessionManager(this)

        // Auto-login se já estiver logado
        if (session.isLoggedIn()) {
            goToProducts()
            return
        }

        binding.btnLogin.setOnClickListener {
            val email = binding.etEmail.text.toString()
            val senha = binding.etSenha.text.toString()
            viewModel.login(email, senha)
        }

        viewModel.uiState.observe(this) { state ->
            when (state) {
                is LoginUiState.Loading -> {
                    binding.progressBar.visible()
                    binding.btnLogin.isEnabled = false
                }
                is LoginUiState.Success -> {
                    binding.progressBar.gone()
                    val r = state.response
                    session.saveSession(
                        token = r.token ?: "",
                        restaurantId = r.restaurantId ?: -1,
                        nome = r.nome ?: ""
                    )
                    goToProducts()
                }
                is LoginUiState.Error -> {
                    binding.progressBar.gone()
                    binding.btnLogin.isEnabled = true
                    binding.root.snack(state.message)
                }
                else -> {
                    binding.progressBar.gone()
                    binding.btnLogin.isEnabled = true
                }
            }
        }
    }

    private fun goToProducts() {
        startActivity(Intent(this, ProductListActivity::class.java))
        finish()
    }
}
