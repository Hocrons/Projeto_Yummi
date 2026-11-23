package com.yummi.restaurante.ui.products

import android.app.AlertDialog
import android.content.Intent
import android.os.Bundle
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import com.yummi.restaurante.data.model.Product
import com.yummi.restaurante.databinding.ActivityProductListBinding
import com.yummi.restaurante.util.SessionManager
import com.yummi.restaurante.util.gone
import com.yummi.restaurante.util.snack
import com.yummi.restaurante.util.visible
import com.yummi.restaurante.ui.login.LoginActivity

class ProductListActivity : AppCompatActivity() {

    private lateinit var binding: ActivityProductListBinding
    private val viewModel: ProductsViewModel by viewModels()
    private lateinit var session: SessionManager
    private lateinit var adapter: ProductAdapter

    private val formLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == RESULT_OK) {
            viewModel.loadProducts(session.bearerToken())
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityProductListBinding.inflate(layoutInflater)
        setContentView(binding.root)

        session = SessionManager(this)

        setupToolbar()
        setupRecyclerView()
        setupFab()
        observeViewModel()

        viewModel.loadProducts(session.bearerToken())
    }

    private fun setupToolbar() {
        setSupportActionBar(binding.toolbar)
        supportActionBar?.title = session.getNome() ?: "Meu Restaurante"
        binding.btnLogout.setOnClickListener { confirmLogout() }
    }

    private fun setupRecyclerView() {
        adapter = ProductAdapter(
            onEdit = { product -> openForm(product) },
            onDelete = { product -> confirmDelete(product) }
        )
        binding.rvProducts.apply {
            layoutManager = LinearLayoutManager(this@ProductListActivity)
            adapter = this@ProductListActivity.adapter
        }
    }

    private fun setupFab() {
        binding.fabAdd.setOnClickListener { openForm(null) }
    }

    private fun openForm(product: Product?) {
        val intent = Intent(this, ProductFormActivity::class.java)
        product?.let { intent.putExtra(ProductFormActivity.EXTRA_PRODUCT_ID, it.id) }
        formLauncher.launch(intent)
    }

    private fun confirmDelete(product: Product) {
        AlertDialog.Builder(this)
            .setTitle("Remover produto")
            .setMessage("Deseja remover \"${product.nome}\"?")
            .setPositiveButton("Remover") { _, _ ->
                viewModel.deleteProduct(session.bearerToken(), product.id)
            }
            .setNegativeButton("Cancelar", null)
            .show()
    }

    private fun confirmLogout() {
        AlertDialog.Builder(this)
            .setTitle("Sair")
            .setMessage("Deseja encerrar a sessão?")
            .setPositiveButton("Sair") { _, _ ->
                session.clearSession()
                startActivity(Intent(this, LoginActivity::class.java))
                finish()
            }
            .setNegativeButton("Cancelar", null)
            .show()
    }

    private fun observeViewModel() {
        viewModel.productsState.observe(this) { state ->
            when (state) {
                is ProductsUiState.Loading -> {
                    binding.progressBar.visible()
                    binding.tvEmpty.gone()
                }
                is ProductsUiState.Success -> {
                    binding.progressBar.gone()
                    adapter.submitList(state.products)
                    if (state.products.isEmpty()) binding.tvEmpty.visible()
                    else binding.tvEmpty.gone()
                }
                is ProductsUiState.Error -> {
                    binding.progressBar.gone()
                    binding.root.snack(state.message)
                }
                else -> binding.progressBar.gone()
            }
        }

        viewModel.actionState.observe(this) { state ->
            when (state) {
                is ProductActionState.Success -> {
                    binding.root.snack(state.message)
                    viewModel.loadProducts(session.bearerToken())
                    viewModel.resetActionState()
                }
                is ProductActionState.Error -> {
                    binding.root.snack(state.message)
                    viewModel.resetActionState()
                }
                else -> {}
            }
        }
    }
}
