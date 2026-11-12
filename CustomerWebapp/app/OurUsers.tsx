'use client'

import { useState, useEffect } from 'react'
import {getAllItems} from './quote/action'

interface Item {
  id: number // or string if using UUID
  created_at: string
  Name: string | null
  Email: string | null
  Address: string | null
  Comments: string | null
}

export function OurUsers(){
    const [items, setItems] = useState<Array<Item> | null>(null)
    
    async function refreshCount() {
        const newItems = await getAllItems()
        setItems(newItems)
    }
    
    useEffect(() => {
        refreshCount()
    }, [])

    return (
        <div>
            {items === null ? <p>'Loading Items...'</p> : null}
            <ul>
                {items === null ? '' : items.map((item) => (
                    <li key={item.id} className="mb-5">
                        {/* Replace with your actual column names */}
                        <strong>{item.Name}</strong> ({item.Email}, {item.Address}): {item.Comments}
                    </li>
                ))}
            </ul>
        </div>
    )
}