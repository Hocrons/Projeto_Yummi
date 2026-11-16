package com.yummi.restaurante.ui.products

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.bumptech.glide.Glide
import com.yummi.restaurante.R
import com.yummi.restaurante.data.model.Product
import com.yummi.restaurante.databinding.ItemProductBinding

class ProductAdapter(
    private val onEdit: (Product) -> Unit,
    private val onDelete: (Product) -> Unit
) : ListAdapter<Product, ProductAdapter.ProductViewHolder>(DiffCallback) {

    companion object DiffCallback : DiffUtil.ItemCallback<Product>() {
        override fun areItemsTheSame(a: Product, b: Product) = a.id == b.id
        override fun areContentsTheSame(a: Product, b: Product) = a == b
    }

    inner class ProductViewHolder(private val binding: ItemProductBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(product: Product) = with(binding) {
            tvNome.text = product.nome
            tvDescricao.text = product.descricao ?: "Sem descrição"
            tvPreco.text = "R$ %.2f".format(product.preco)
            chipDisponivel.text = if (product.disponivel) "Disponível" else "Indisponível"
            chipDisponivel.setChipBackgroundColorResource(
                if (product.disponivel) R.color.chip_available_bg else R.color.chip_unavailable_bg
            )

            if (!product.fotoUrl.isNullOrBlank()) {
                Glide.with(ivFoto)
                    .load(product.fotoUrl)
                    .placeholder(R.drawable.ic_food_placeholder)
                    .centerCrop()
                    .into(ivFoto)
            } else {
                ivFoto.setImageResource(R.drawable.ic_food_placeholder)
            }

            btnEdit.setOnClickListener { onEdit(product) }
            btnDelete.setOnClickListener { onDelete(product) }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int) =
        ProductViewHolder(
            ItemProductBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        )

    override fun onBindViewHolder(holder: ProductViewHolder, position: Int) =
        holder.bind(getItem(position))
}
