'use server'

'use server'

import { createClient } from '@/utils/supabase/server'
import { revalidatePath } from 'next/cache'

// database password : t3sT$2mOla0#&71

export async function getAllItems(){
    const supabase = await createClient();

    const { data, error } = await supabase
        .from('Quotes')
        .select('*')
        .order('created_at', { ascending: false });
    
    if(error){
        console.error('Error fetching data: ', error.message);
        return [];
    }

    return data ?? [];
}

export async function getRowCount(): Promise<number> {
    const supabase = await createClient()

    const { count, error } = await supabase
        .from('Quotes')
        .select('*', { count: 'exact', head: true })

    if (error) {
        console.error('Error getting row count:', error.message)
        return 0
    }

    return count ?? 0
}

export async function askQuote(formData: FormData) {
    // Extract data using the input's 'name' attribute
    const name = formData.get('name') as string;
    const email = formData.get('email') as string;
    const address = formData.get('address') as string;
    const comments = formData.get('comments') as string;

    const supabase = await createClient()

    // Extract data from FormData or pass an object directly

    // Append a single row (pass an array of objects to insert multiple rows)
    const { data, error } = await supabase
        .from('Quotes')
        .insert({
            Name: name,
            Email: email,
            Address: address,
            Comments: comments
        })
        .select() // Optional: returns the newly created row(s)

    if (error) {
        console.error('Error inserting row:', error.message)
    }

    // Refresh cached page data so the UI shows the new row
    revalidatePath('/')

    console.log(data);
}