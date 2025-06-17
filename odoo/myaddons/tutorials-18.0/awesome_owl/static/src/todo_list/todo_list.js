/** @odoo-module **/

import { Component,useState } from "@odoo/owl";
import { TodoItem } from './todo_item';

export class TodoList extends Component {
   static template = "awesome_owl.todo_list";
   static components = { TodoItem };

   setup() {
   // in TodoList
    this.todos = useState([{ id: 1, description: "buy milk", isCompleted: true },
    { id: 2, description: "buy drink", isCompleted: false },
    { id: 3, description: "buy cakes", isCompleted: false },
    ]);
   }
}
