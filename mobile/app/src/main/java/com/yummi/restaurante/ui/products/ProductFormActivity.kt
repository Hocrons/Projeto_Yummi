package com.yummi.restaurante.ui.products

import android.os.Bundle
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import com.yummi.restaurante.data.model.Product
import com.yummi.restaurante.databinding.ActivityProductFormBinding
import com.yummi.restaurante.util.SessionManager
import com.yummi.restaurante.util.gone
import com.yummi.restaurante.util.snack
import com.yummi.restaurante.util.visible

class ProductFormActivity : AppCompatActivity() {

    companion object {
        const val EXTRA_PRODUCT_ID = "extra_product_id"
    }

    private lateinit var binding: ActivityProductFormBinding
    private val viewModel: ProductsViewModel by viewModels()
    private lateinit var session: SessionManager

    // Produto sendo editado (null = novo)
    private var editingProduct: Product? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityProductFormBinding.inflate(layoutInflater)
        setContentView(binding.root)

        session = SessionManager(this)

        val productId = intent.getIntExtra(EXTRA_PRODUCT_ID, -1)
        val isEditing = productId != -1

        setupToolbar(isEditing)
        setupSaveButton(isEditing, productId)
        observeViewModel()

        // Se editando, carrega os produtos e pré-preenche o formulário
        if (isEditing) {
            viewModel.loadProducts(session.bearerToken())
            viewModel.productsState.observe(this) { state ->
                if (state is ProductsUiState.Success) {
                    val product = state.products.find { it.id == productId }
                    product?.let { fillForm(it) }
                }
            }
        }
    }

    private fun setupToolbar(isEditing: Boolean) {
        setSupportActionBar(binding.toolbar)
        supportActionBar?.apply {
            title = if (isEditing) "Editar Produto" else "Novo Produto"
            setDisplayHomeAsUpEnabled(true)
        }
        binding.toolbar.setNavigationOnClickListener { finish() }
    }

    private fun fillForm(product: Product) {
        editingProduct = product
        binding.etNome.setText(product.nome)
        binding.etDescricao.setText(product.descricao ?: "")
        binding.etPreco.setText("%.2f".format(product.preco))
        binding.etFotoUrl.setText(product.fotoUrl ?: "")
        binding.switchDisponivel.isChecked = product.disponivel
    }

    private fun setupSaveButton(isEditing: Boolean, productId: Int) {
        binding.btnSalvar.setOnClickListener {
            val nome = binding.etNome.text.toString().trim()
            val descricao = binding.etDescricao.text.toString().trim()
            val precoStr = binding.etPreco.text.toString().trim()
            val fotoUrl = binding.etFotoUrl.text.toString().trim()
            val disponivel = binding.switchDisponivel.isChecked

            if (nome.isBlank()) {
                binding.tilNome.error = "Nome obrigatório"
                return@setOnClickListener
            }
            binding.tilNome.error = null

            val preco = precoStr.replace(",", ".").toDoubleOrNull()
            if (preco == null || preco < 0) {
                binding.tilPreco.error = "Preço inválido"
                return@setOnClickListener
            }
            binding.tilPreco.error = null

            val product = Product(
                id = if (isEditing) productId else 0,
                restaurantId = session.getRestaurantId(),
                nome = nome,
                descricao = descricao.ifBlank { null },
                preco = preco,
                disponivel = disponivel,
                fotoUrl = fotoUrl.ifBlank { null }
            )

            if (isEditing) {
                viewModel.updateProduct(session.bearerToken(), product)
            } else {
                viewModel.createProduct(session.bearerToken(), product)
            }
        }
    }

    private fun observeViewModel() {
        viewModel.actionState.observe(this) { state ->
            when (state) {
                is ProductActionState.Loading -> {
                    binding.progressBar.visible()
                    binding.btnSalvar.isEnabled = false
                }
                is ProductActionState.Success -> {
                    binding.progressBar.gone()
                    setResult(RESULT_OK)
                    finish()
                }
                is ProductActionState.Error -> {
                    binding.progressBar.gone()
                    binding.btnSalvar.isEnabled = true
                    binding.root.snack(state.message)
                }
                else -> {
                    binding.progressBar.gone()
                    binding.btnSalvar.isEnabled = true
                }
            }
        }
    }
}
